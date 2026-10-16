#!/usr/bin/env python3
"""PyMem: a spaced-repetition trainer for Python basics and idioms.

    python pymem.py              today's review session
    python pymem.py stats        your progress per topic
    python pymem.py --help       everything else

Answers are checked by actually running Python. Progress is saved to
~/.pymem_progress.json (override with --data or $PYMEM_DATA).
"""

from __future__ import annotations

import argparse
import ast
import builtins
import collections.abc
import contextlib
import datetime as dt
import io
import json
import keyword
import os
import random
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import tokenize

from cards import CARDS, TOPICS

try:
    import readline  # line editing, history (up arrow) and auto-indent; missing on Windows
except ImportError:
    readline = None

if os.name == "nt":
    os.system("")  # enables ANSI colours in the Windows console
with contextlib.suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(errors="replace")

# --------------------------------------------------------------------------- look & feel

COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ


def _style(code):
    return lambda text: f"\033[{code}m{text}\033[0m" if COLOR else str(text)


bold, dim, red, green, yellow, blue, magenta, cyan = (
    _style(c) for c in ("1", "2", "31", "32", "33", "34", "35", "36"))

KIND_LABEL = {"concept": "recall", "output": "predict the output",
              "expr": "one-liner", "code": "write code"}
PRAISE = ["Nailed it!", "Correct!", "Yes! 💪", "Spot on!", "Perfect."]
BUILTIN_NAMES = set(dir(builtins))
FSTRING_TOKENS = {getattr(tokenize, n) for n in ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END")
                  if hasattr(tokenize, n)}


def width():
    return min(shutil.get_terminal_size().columns, 76)


def rule(label=""):
    if not label:
        return dim("─" * width())
    return dim(f"── {label} ".ljust(width(), "─"))


def highlight(src):
    """Tiny syntax highlighter built on the tokenize module."""
    if not COLOR:
        return src
    starts = [0]
    for line in src.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))

    def offset(pos):
        return starts[pos[0] - 1] + pos[1] if pos[0] - 1 < len(starts) else len(src)

    out, last, prev = [], 0, ""
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.ENDMARKER:
                break
            start, end = offset(tok.start), offset(tok.end)
            if start < last or end < start:
                continue
            paint = None
            if tok.type == tokenize.NAME:
                if keyword.iskeyword(tok.string):
                    paint = magenta
                elif prev in ("def", "class"):
                    paint = blue
                elif tok.string in BUILTIN_NAMES:
                    paint = cyan
            elif tok.type == tokenize.STRING or tok.type in FSTRING_TOKENS:
                paint = green
            elif tok.type == tokenize.NUMBER:
                paint = yellow
            elif tok.type == tokenize.COMMENT:
                paint = dim
            text = src[start:end]
            out.append(src[last:start])
            out.append("\n".join(paint(part) for part in text.split("\n")) if paint else text)
            last = end
            if tok.type == tokenize.NAME:
                prev = tok.string
    except (tokenize.TokenError, SyntaxError):
        return src
    out.append(src[last:])
    return "".join(out)


def code_block(src):
    return "\n".join(dim("  │ ") + line for line in highlight(src.rstrip("\n")).split("\n"))


def why_text(text):
    first, *rest = text.splitlines()
    return "\n".join([yellow("💡 ") + first] + ["   " + line for line in rest])


def short_repr(value, limit=150):
    text = repr(value)
    if isinstance(value, (set, frozenset)) and value:
        with contextlib.suppress(TypeError):  # show sets sorted, so the display is stable
            text = "{" + ", ".join(map(repr, sorted(value))) + "}"
    return text if len(text) <= limit else text[:limit - 1] + "…"


def exc_text(err):
    if isinstance(err, SyntaxError):
        return f"SyntaxError: {err.msg} (line {err.lineno})"
    return f"{type(err).__name__}: {err}" if str(err) else type(err).__name__


# --------------------------------------------------------------------------- running code

TIME_LIMIT = 3  # seconds


class Timeout(BaseException):  # BaseException so `except Exception` in user code can't swallow it
    pass


@contextlib.contextmanager
def time_limit(seconds):
    if not hasattr(signal, "SIGALRM"):  # Windows: no limit
        yield
        return

    def on_alarm(signum, frame):
        raise Timeout(f"took longer than {seconds}s. Infinite loop?")

    old = signal.signal(signal.SIGALRM, on_alarm)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def execute(source, ns, mode="exec"):
    """Run source in namespace ns. Returns (value, captured stdout, exception or None)."""
    buf = io.StringIO()
    value = error = None
    with contextlib.redirect_stdout(buf):
        try:
            with time_limit(TIME_LIMIT):
                compiled = compile(source, "<your code>", mode)
                value = eval(compiled, ns) if mode == "eval" else exec(compiled, ns)
        except BaseException as err:  # user code may raise anything, even SystemExit or Ctrl+C
            error = err
    return value, buf.getvalue(), error


def new_namespace():
    return {"__name__": "__main__"}


def raises(exc_type, func, *args, **kwargs):
    """Test helper for code cards: True if func(*args, **kwargs) raises exc_type."""
    try:
        func(*args, **kwargs)
    except exc_type:
        return True
    return False


def snippet_output(snippet):
    """The lines a snippet prints; if it raises, the last line is the exception name."""
    _, out, err = execute(snippet, new_namespace())
    text = out.rstrip("\n")
    lines = [line.rstrip() for line in text.split("\n")] if text else []
    if err is not None:
        lines.append(type(err).__name__)
    return lines, err


def reference_value(card, setup):
    ns = new_namespace()
    execute(setup, ns)
    value, _, err = execute(card.answer, ns, "eval")
    return value, err


def check_expr(card, user):
    try:
        compile(user, "<expr>", "eval")
    except SyntaxError as err:
        hint = " (I need an expression, not an assignment)" if "=" in user else ""
        return False, f"not a valid expression: {err.msg}{hint}"
    for n, setup in enumerate((card.code,) + card.alt):
        want, _ = reference_value(card, setup)
        ns = new_namespace()
        execute(setup, ns)
        got, _, err = execute(user, ns, "eval")
        if err is not None:
            return False, exc_text(err) + ("  (with a different input)" if n else "")
        if got != want:
            if n == 0:
                msg = f"got {short_repr(got)}"
                if isinstance(got, collections.abc.Iterator):
                    msg += ". That's a lazy iterator; wrap it in list(...)?"
                return False, msg
            return False, (f"right for the example, but with  {setup.replace(chr(10), '; ')}\n"
                           f"  it gives {short_repr(got)} instead of {short_repr(want)}. No hard-coding 😉")
        if card.check:
            try:
                passed = eval(card.check, {"result": got})
            except Exception:
                passed = False
            if not passed:
                return False, card.check_msg or "close, but it fails an extra check"
    return True, ""


def actual_side(test, ns):
    """For a failing `left == right` test, show what `left` evaluated to."""
    try:
        node = ast.parse(test, mode="eval").body
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], (ast.Eq, ast.Is)):
            left = ast.get_source_segment(test, node.left)
            value, _, err = execute(left, ns, "eval")
            if err is None:
                return f"\n  {left} gave {short_repr(value)}"
    except (SyntaxError, ValueError):
        pass
    return ""


def check_code(card, src):
    ns = new_namespace()
    ns["raises"] = raises
    printed = ""
    for label, source in (("setup", card.code), ("your code", src), ("test setup", card.after)):
        if not source:
            continue
        _, out, err = execute(source, ns)
        printed += out
        if err is not None:
            if label == "your code":
                return False, f"your code raised {exc_text(err)}"
            return False, f"{label} failed: {exc_text(err)}"
    for test in card.tests:
        value, out, err = execute(test, ns, "eval")
        printed += out
        if err is not None:
            msg = f"{test}\n  raised {exc_text(err)}"
        elif not value:
            msg = f"failed: {test}{actual_side(test, ns)}"
        else:
            continue
        if printed.strip():
            msg += "\n" + dim("  your code printed: " + short_repr(printed.strip(), 200))
        return False, msg
    return True, ""


# --------------------------------------------------------------------------- input


class Quit(Exception):
    def __init__(self, grade=None):
        super().__init__()
        self.grade = grade  # a grade to record before quitting, if any


def read(prompt="› ", prefill=""):
    hook = readline is not None and prefill and hasattr(readline, "set_pre_input_hook")
    if hook:
        def insert():
            readline.insert_text(prefill)
            readline.redisplay()
        readline.set_pre_input_hook(insert)
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        raise Quit from None
    finally:
        if hook:
            readline.set_pre_input_hook()


def next_indent(lines):
    """Auto-indent like an editor: keep the last indent, add 4 after a ':'."""
    if readline is None:
        return ""
    for line in reversed(lines):
        if line.strip():
            indent = line[:len(line) - len(line.lstrip())]
            return indent + "    " if line.rstrip().endswith(":") else indent
    return ""


def edit_in_editor(text):
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or ("notepad" if os.name == "nt" else "nano")
    fd, path = tempfile.mkstemp(suffix=".py", prefix="pymem_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        subprocess.call(shlex.split(editor, posix=os.name != "nt") + [path])
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError as err:
        print(red(f"couldn't run editor {editor!r}: {err}. Set $EDITOR."))
        return None
    finally:
        with contextlib.suppress(OSError):
            os.unlink(path)


def read_code(draft=""):
    """Read a block of code. An empty line submits (two in a row after an indented line).

    Returns the source, or None if the user asked to see the answer.
    """
    lines = []
    while True:
        line = read(">>> " if not lines else "... ", prefill=next_indent(lines)).expandtabs(4)
        cmd = line.strip()
        if cmd == ":q":
            raise Quit
        if cmd == ":s":
            return None
        if cmd == ":e":
            text = edit_in_editor("\n".join(lines) + "\n" if lines else draft)
            if text and text.strip():
                print(code_block(text))
                return text
            continue
        if not cmd:
            if not lines:
                continue
            if not lines[-1].strip() or not lines[-1][0].isspace():
                break
            lines.append("")
            continue
        lines.append(line.rstrip())
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- asking one card

AGAIN, HARD, GOOD, EASY = range(4)


def praise(note=""):
    print(green("✓ " + random.choice(PRAISE)) + (dim(f"  ({note})") if note else ""))


def self_grade():
    while True:
        choice = read("How well did you know it?  1 again · 2 hard · 3 good · 4 easy › ").strip()
        if choice == ":q":
            raise Quit
        if choice in ("1", "2", "3", "4"):
            return int(choice) - 1


def after_miss(gave_up):
    if gave_up:
        read("Enter to continue › ")
        return AGAIN
    choice = read("Enter = continue · o = I was actually right (just a typo) › ").strip().lower()
    if choice == ":q":
        raise Quit(AGAIN)
    return GOOD if choice == "o" else AGAIN


def show_why(card):
    if card.why:
        print(why_text(card.why))


def ask_concept(card):
    print(bold(card.q))
    typed = read("your answer (or just Enter to reveal) › ").strip()
    if typed == ":q":
        raise Quit
    print(rule("answer"))
    print(card.answer)
    show_why(card)
    return self_grade()


def _same(a, b):
    return "".join(a.split()) == "".join(b.split())


def ask_output(card):
    print(bold("What does this print?"))
    print(code_block(card.code))
    expected, err = snippet_output(card.code)
    n = len(expected)
    print(dim(f"{n} line{'s' if n != 1 else ''} of output · if it raises, type the exception name "
              f"(e.g. TypeError) · :s = show"))
    got = []
    for k in range(n):
        line = read(f"{k + 1}› " if n > 1 else "› ")
        if line.strip() == ":q":
            raise Quit
        if line.strip() == ":s":
            got = None
            break
        got.append(line.rstrip())

    if got is not None:
        if err is not None and got[-1].strip().split(":")[0].strip() == expected[-1]:
            got[-1] = expected[-1]  # accept "TypeError: message" too
        if got == expected or [g.strip() for g in got] == [e.strip() for e in expected]:
            praise()
            show_why(card)
            return GOOD
        if all(_same(g, e) for g, e in zip(got, expected)):
            praise("only the spacing differs:")
            print("\n".join(dim("  │ ") + green(line) for line in expected))
            show_why(card)
            return GOOD
        print(red("✗ Not quite. Actual output:"))
    else:
        print(dim("Actual output:"))
    for i, line in enumerate(expected):
        print(dim("  │ ") + green(line))
        if got is not None and not _same(got[i], line):
            print(dim("  │ ") + red(f"{got[i].strip()}   ← yours"))
    show_why(card)
    return after_miss(gave_up=got is None)


def ask_expr(card):
    print(bold(card.q))
    if card.code:
        print(code_block(card.code))
    target, _ = reference_value(card, card.code)
    print(f"{dim('target →')} {green(short_repr(target))}")
    print(dim("Type one expression · :s = show answer"))
    gave_up = False
    for attempt in (1, 2):
        line = ""
        while not line:
            line = read("› ").strip()
        if line == ":q":
            raise Quit
        if line == ":s":
            gave_up = True
            break
        ok, msg = check_expr(card, line)
        if ok:
            praise()
            if "".join(line.split()) != "".join(card.answer.split()):
                print(f"{dim('reference:')} {highlight(card.answer)}")
            show_why(card)
            return GOOD if attempt == 1 else HARD
        print(red("✗ " + msg))
        if attempt == 1:
            print(dim("One more try" + (" (↑ recalls your answer)." if readline else ".")))
    print(f"{dim('answer:')} {highlight(card.answer)}")
    show_why(card)
    return after_miss(gave_up)


def ask_code(card):
    print(bold(card.q))
    if card.code:
        print(dim("given:"))
        print(code_block(card.code))
    print(dim("Type your code · an empty line submits (press Enter twice after an indented block)\n"
              ":e = write it in your $EDITOR · :s = show answer"))
    draft, gave_up = "", False
    for attempt in (1, 2):
        src = read_code(draft)
        if src is None:
            gave_up = True
            break
        ok, msg = check_code(card, src)
        if ok:
            praise(f"all {len(card.tests)} tests pass")
            print(dim("reference solution:"))
            print(code_block(card.answer))
            show_why(card)
            return GOOD if attempt == 1 else HARD
        print(red("✗ " + msg))
        draft = src
        if attempt == 1:
            print(dim("One more try. :e opens your last attempt in an editor."))
    print(dim("reference solution:"))
    print(code_block(card.answer))
    show_why(card)
    return after_miss(gave_up)


ASK = {"concept": ask_concept, "output": ask_output, "expr": ask_expr, "code": ask_code}

# --------------------------------------------------------------------------- scheduling (Leitner boxes)

INTERVALS = [0, 1, 3, 7, 14, 30]  # days until the next review, indexed by box
MASTERED = len(INTERVALS) - 1


def reschedule(rec, grade, today):
    box = rec.get("box", 0)
    if grade == AGAIN:
        box, days = 0, 0
    elif grade == HARD:
        box = max(box, 1)
        days = max(1, INTERVALS[box] // 2)
    else:
        box = min(box + (2 if grade == EASY else 1), MASTERED)
        days = INTERVALS[box]
    rec["box"] = box
    rec["due"] = (today + dt.timedelta(days=days)).isoformat()
    rec["seen"] = rec.get("seen", 0) + 1
    rec["right"] = rec.get("right", 0) + (grade != AGAIN)


class Progress:
    def __init__(self, path):
        self.path = path
        self.data = {"version": 1, "cards": {}, "history": {}}
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    self.data.update(json.load(f))
            except (OSError, ValueError) as err:
                sys.exit(f"Can't read progress file {path}: {err}")

    @property
    def cards(self):
        return self.data["cards"]

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=1, sort_keys=True)
        os.replace(tmp, self.path)

    def log_review(self, today, count=1):
        history = self.data["history"]
        history[today.isoformat()] = history.get(today.isoformat(), 0) + count

    def streak(self, today):
        history = self.data["history"]
        day = today if today.isoformat() in history else today - dt.timedelta(days=1)
        count = 0
        while day.isoformat() in history:
            count += 1
            day -= dt.timedelta(days=1)
        return count

    def streak_text(self, today):
        n = self.streak(today)
        return f"🔥 {n}-day streak" if n else "🌱 start a streak today"

    def due_on_or_before(self, pool, day):
        return [c for c in pool if c.id in self.cards and self.cards[c.id]["due"] <= day.isoformat()]


def interleave(cards):
    """Round-robin across topics, keeping each topic's authored (easy-first) order."""
    by_topic = {}
    for card in cards:
        by_topic.setdefault(card.topic, []).append(card)
    queues, out = list(by_topic.values()), []
    while queues:
        for queue in queues:
            out.append(queue.pop(0))
        queues = [q for q in queues if q]
    return out


def build_session(pool, progress, today, size, new_limit):
    due = sorted(progress.due_on_or_before(pool, today), key=lambda c: progress.cards[c.id]["due"])
    fresh = interleave([c for c in pool if c.id not in progress.cards])
    session = due[:size]
    session += fresh[:max(0, min(new_limit, size - len(session)))]
    random.shuffle(session)
    return session, len(due), len(fresh)


def run_session(queue, progress, today, cram=False):
    results, retried, i = [], set(), 0
    while i < len(queue):
        card = queue[i]
        rec = progress.cards.get(card.id)
        status = "new" if rec is None else f"box {rec['box']}/{MASTERED}"
        print()
        print(rule())
        print(f"{bold(f'[{i + 1}/{len(queue)}]')} {cyan(TOPICS[card.topic])} "
              f"{dim('·')} {KIND_LABEL[card.kind]} {dim('· ' + status)}")
        print()
        quit_after = False
        try:
            grade = ASK[card.kind](card)
        except Quit as stop:
            if stop.grade is None:
                break
            grade, quit_after = stop.grade, True
        results.append((card, grade))
        if not cram:
            reschedule(progress.cards.setdefault(card.id, {}), grade, today)
        progress.log_review(today)
        progress.save()
        if quit_after:
            break
        if grade == AGAIN and card.id not in retried:
            retried.add(card.id)
            queue.append(card)
            print(dim("↻ This one comes back at the end of the session."))
        i += 1
    return results


def print_summary(results, progress, pool, today, cram):
    print()
    print(rule("session done"))
    if not results:
        print("No cards answered. See you soon!")
        return
    right = sum(grade != AGAIN for _, grade in results)
    pct = 100 * right // len(results)
    mood = "🔥 Amazing!" if pct >= 90 else "💪 Good work!" if pct >= 70 else "🌱 Every miss is a memory in the making."
    print(f"{bold(f'{right}/{len(results)} correct ({pct}%)')}  {mood}")
    missed = sorted({c.id for c, grade in results if grade == AGAIN})
    if missed:
        print(dim("Missed: " + ", ".join(missed)))
    if not cram:
        mastered = sum(progress.cards.get(c.id, {}).get("box") == MASTERED for c in pool)
        tomorrow = today + dt.timedelta(days=1)
        due_tomorrow = len(progress.due_on_or_before(pool, tomorrow))
        print(f"Mastered {mastered}/{len(pool)} cards · {due_tomorrow} due by tomorrow "
              f"({tomorrow.strftime('%a %d %b')})")
    print(progress.streak_text(today))


# --------------------------------------------------------------------------- commands


def resolve_topics(spec):
    if not spec:
        return None
    chosen = set()
    for part in (p.strip().lower() for p in spec.split(",")):
        matches = [part] if part in TOPICS else [k for k in TOPICS if k.startswith(part)]
        if not matches:
            sys.exit(f"Unknown topic {part!r}. Topics: {', '.join(TOPICS)}")
        chosen.update(matches)
    return chosen


def card_pool(topics):
    return [c for c in CARDS if sys.version_info >= c.min_py and (topics is None or c.topic in topics)]


def cmd_review(args, progress, pool, today, cram=False):
    if cram:
        queue = random.sample(pool, min(args.size, len(pool)))
        due_count = new_count = 0
    else:
        queue, due_count, new_count = build_session(pool, progress, today, args.size, args.new)
    print(bold(f"PyMem · {today.strftime('%A, %d %b %Y')}") + f" · {progress.streak_text(today)}")
    if not queue:
        progress.log_review(today, count=0)  # showing up on a day with nothing due keeps the streak
        progress.save()
        upcoming = sorted(progress.cards[c.id]["due"] for c in pool if c.id in progress.cards)
        when = dt.date.fromisoformat(upcoming[0]).strftime("%A %d %b") if upcoming else "never"
        print(f"🎉 Nothing due right now, you're all caught up! Next review: {when}.")
        print(dim("Want extra practice? Try `python pymem.py cram` or raise --new."))
        return
    if cram:
        print(f"Cram mode: {len(queue)} random cards. Practice only, your schedule isn't touched.")
    else:
        fresh_today = sum(c.id not in progress.cards for c in queue)
        print(f"{len(queue) - fresh_today} due + {fresh_today} new = {bold(str(len(queue)))} cards "
              + dim(f"(still waiting: {due_count - (len(queue) - fresh_today)} due, {new_count - fresh_today} new)"))
    print(dim("Commands: :s = show the answer · :q = quit (progress is saved after every card)"))
    results = run_session(queue, progress, today, cram)
    print_summary(results, progress, pool, today, cram)


def cmd_stats(progress, pool, today):
    print(bold(f"PyMem progress · {today.strftime('%A, %d %b %Y')}"))
    print(dim("bar: █ mastered  ▓ reviewing  ░ learning  · new"))
    print()
    bar_len = 20
    for key, title in TOPICS.items():
        cards = [c for c in pool if c.topic == key]
        if not cards:
            continue
        boxes = [progress.cards[c.id]["box"] if c.id in progress.cards else None for c in cards]
        counts = {
            "█": sum(b == MASTERED for b in boxes),
            "▓": sum(b is not None and 2 <= b < MASTERED for b in boxes),
            "░": sum(b is not None and b <= 1 for b in boxes),
        }
        counts["·"] = len(cards) - sum(counts.values())
        bar = "".join(ch * round(n * bar_len / len(cards)) for ch, n in counts.items())[:bar_len].ljust(bar_len, "·")
        seen = sum(progress.cards[c.id].get("seen", 0) for c in cards if c.id in progress.cards)
        right = sum(progress.cards[c.id].get("right", 0) for c in cards if c.id in progress.cards)
        acc = f"{100 * right // seen:3d}%" if seen else "   –"
        print(f"{key:<15}{green(bar)} {counts['█']:>2}/{len(cards):<3} mastered   accuracy {acc}")
    print()
    mastered = sum(progress.cards.get(c.id, {}).get("box") == MASTERED for c in pool)
    started = sum(c.id in progress.cards for c in pool)
    due_now = len(progress.due_on_or_before(pool, today))
    due_week = len(progress.due_on_or_before(pool, today + dt.timedelta(days=7)))
    reviews = sum(progress.data["history"].values())
    print(f"Cards: {len(pool)} total · {started} started · {bold(str(mastered))} mastered")
    print(f"Due: {due_now} now · {due_week} within 7 days")
    active_days = sum(n > 0 for n in progress.data["history"].values())
    print(f"Reviews: {reviews} on {active_days} day(s) · {progress.streak_text(today)}")


def cmd_topics(pool):
    for key, title in TOPICS.items():
        n = sum(c.topic == key for c in pool)
        print(f"{key:<15}{n:>3} cards  {dim(title)}")


def cmd_browse(pool):
    """A printable study sheet: every card with its answer."""
    for card in pool:
        print(rule(f"{card.id} · {KIND_LABEL[card.kind]}"))
        if card.kind == "concept":
            print(bold(card.q))
            print(card.answer)
        elif card.kind == "output":
            print(code_block(card.code))
            print(dim("output:"))
            print("\n".join(dim("  │ ") + green(line) for line in snippet_output(card.code)[0]))
        elif card.kind == "expr":
            print(bold(card.q))
            print(code_block(card.code))
            value, _ = reference_value(card, card.code)
            print(f"{dim('answer:')} {highlight(card.answer)}   {dim('→')} {green(short_repr(value))}")
        else:
            print(bold(card.q))
            if card.code:
                print(code_block(card.code))
            print(code_block(card.answer))
        show_why(card)
        print()


def cmd_reset(progress):
    if not os.path.exists(progress.path):
        print("Nothing to reset.")
        return
    if read(f"Delete all progress in {progress.path}? Type 'yes' › ").strip().lower() == "yes":
        os.remove(progress.path)
        print("Progress cleared. Fresh start! 🌱")
    else:
        print("Kept your progress.")


def cmd_selftest():
    """Check every card: unique ids, runnable snippets, reference answers pass their own checks."""
    problems, skipped, seen = [], 0, set()
    for card in CARDS:
        where = f"{card.id}:"
        if card.id in seen:
            problems.append(f"{where} duplicate id")
        seen.add(card.id)
        if card.topic not in TOPICS or card.kind not in ASK:
            problems.append(f"{where} bad topic/kind")
            continue
        if sys.version_info < card.min_py:
            skipped += 1
            continue
        if card.kind == "concept":
            if not (card.q and card.answer):
                problems.append(f"{where} missing question or answer")
        elif card.kind == "output":
            lines, err = snippet_output(card.code)
            if isinstance(err, Timeout) or not lines:
                problems.append(f"{where} snippet timed out or printed nothing")
        elif card.kind == "expr":
            for setup in (card.code,) + card.alt:
                _, err = reference_value(card, setup)
                if err is not None:
                    problems.append(f"{where} reference raised {exc_text(err)}")
            ok, msg = check_expr(card, card.answer)
            if not ok:
                problems.append(f"{where} reference fails its own check: {msg}")
        elif card.kind == "code":
            ok, msg = check_code(card, card.answer)
            if not ok:
                problems.append(f"{where} reference solution fails: {msg}")
    for problem in problems:
        print(red("✗ " + problem))
    print(f"{len(CARDS)} cards checked, {skipped} skipped (need a newer Python), {len(problems)} problem(s).")
    return 1 if problems else 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="pymem.py",
        description="Spaced-repetition trainer for Python basics and idioms.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""commands:
  review    today's session: due cards + a few new ones (default)
  cram      random practice that doesn't touch your schedule
  stats     progress per topic
  topics    list the topics
  browse    print every card with its answer (a study sheet)
  reset     delete your progress
  selftest  check that every card in the bank works

examples:
  python pymem.py
  python pymem.py -t functions,oop -n 10
  python pymem.py cram -t idioms
  python pymem.py browse -t stdlib | less -R""")
    parser.add_argument("command", nargs="?", default="review",
                        choices=["review", "cram", "stats", "topics", "browse", "reset", "selftest"])
    parser.add_argument("-t", "--topic", help="only these topics (comma-separated; prefixes work)")
    parser.add_argument("-n", "--size", type=int, default=20, help="max cards per session (default 20)")
    parser.add_argument("--new", type=int, default=8, help="max new cards per session (default 8)")
    parser.add_argument("--data", default=os.environ.get("PYMEM_DATA") or os.path.join(
        os.path.expanduser("~"), ".pymem_progress.json"), help="progress file")
    args = parser.parse_args(argv)

    # PYMEM_TODAY=YYYY-MM-DD pretends it's another day (handy for testing the scheduler)
    today = dt.date.fromisoformat(os.environ["PYMEM_TODAY"]) if os.environ.get("PYMEM_TODAY") else dt.date.today()
    pool = card_pool(resolve_topics(args.topic))
    if args.command == "selftest":
        return cmd_selftest()
    if args.command == "topics":
        return cmd_topics(pool)
    if args.command == "browse":
        return cmd_browse(pool)
    progress = Progress(args.data)
    if args.command == "reset":
        with contextlib.suppress(Quit):
            cmd_reset(progress)
        return None
    if args.command == "stats":
        return cmd_stats(progress, pool, today)
    return cmd_review(args, progress, pool, today, cram=args.command == "cram")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # e.g. `pymem.py browse | head`
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(1)
