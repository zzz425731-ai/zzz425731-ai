# PyMem: a Python memory trainer

A small terminal app that drills Python fundamentals and idioms with **spaced repetition**.
Every answer is checked by **actually running Python**, so the feedback is always right.

- 135 cards across 14 topics, from `//` vs C++ division to closures, generators, dataclasses and `heapq`
- Four card types: recall, predict the output, one-liners and write-the-code
- Short explanations after every card, many with **"C++:"** notes on where Python behaves differently
- No dependencies. Python 3.8+ (a few cards need 3.9/3.10 and are skipped on older versions)

## Quick start

```bash
cd python-memory-trainer
python pymem.py            # today's session (~20 cards, takes 10–15 minutes)
python pymem.py stats      # how you're doing per topic
```

Do one session a day. The app decides what you see: cards you keep getting right
show up less and less often, and cards you miss come back quickly.

## On your iPhone (web version)

`web/` holds a phone-first web version with the same 135 cards and the same box schedule.
One-liners and code answers are still checked by real Python, running in the browser
(Pyodide, about 14 MB, downloaded once). If a browser blocks that, the app shows the
reference answer and you grade yourself. Typing code is phone-friendly: a key bar for
Tab, brackets and colons; Return auto-indents; iOS curly quotes are straightened before checking.

```bash
python web/build.py        # writes web/dist/ (cards data, worker, Pyodide)
cd web/dist && python -m http.server 8000   # then open http://<your-computer>:8000 on the phone
```

**Your progress is saved after every answer.** The web version stores it as a log of
what you did (each review, typo fix, reset or import), and works out boxes and due dates by
replaying that log. Copies on different devices or tabs are combined by joining their logs, so
studying on your phone and laptop on the same day never loses a review. Inside claude.ai the
log is also kept in your private per-account store (one small document per month), so it
follows you between devices; without an account it stays in the browser.
**Settings → Export backup** saves a file in the same format as the terminal's
`~/.pymem_progress.json`, and **Import** reads either one.

## The four card types

| Type | You do | Checked by |
| --- | --- | --- |
| **recall** | answer a concept question in your head (or type it), reveal, then grade yourself 1–4 | you |
| **predict the output** | read a snippet and type exactly what it prints (`TypeError` etc. if it raises) | running the snippet |
| **one-liner** | write one expression that produces the target value | evaluating it on the shown input **and** hidden inputs, so no hard-coding 😉 |
| **write code** | write a function or class at a REPL-style prompt | running tests against it |

Typing code: the prompt auto-indents (Linux/macOS). **An empty line submits**; after an indented line,
press Enter twice. Type `:e` to write the answer in your `$EDITOR` instead.

Keys at any prompt: `:s` shows the answer, `:q` quits (progress is saved after every card).
If the checker marks you wrong for a typo, press `o` to override.

## Why it works

- **Active recall**: producing an answer (not re-reading notes) is what builds memory.
- **Spaced repetition (Leitner boxes)**: each card lives in a box from 0 to 5.

  | box | 0 | 1 | 2 | 3 | 4 | 5 (mastered) |
  | --- | - | - | - | - | - | - |
  | next review in | today | 1 day | 3 days | 7 days | 14 days | 30 days |

  Right → up one box (`easy` on recall cards: up two). Wrong → back to box 0, and it comes back later in the same session.
  `hard` keeps the card in its box with a shorter wait.
- **Interleaving**: new cards rotate through the topics instead of drilling one topic at a time,
  which feels harder but sticks better.
- **Desirable difficulty**: the snippets target classic traps (mutable default arguments,
  `[[0] * 3] * 3`, late-binding closures, ...), because a mistake you've made once is hard to forget.

## Commands

```bash
python pymem.py                       # review: due cards + up to 8 new ones
python pymem.py -t functions,oop      # only some topics (prefixes work: -t func)
python pymem.py -n 10 --new 3         # shorter session, fewer new cards
python pymem.py cram -t idioms        # random practice, doesn't touch your schedule
python pymem.py stats                 # progress bars, accuracy, streak
python pymem.py topics                # list topics
python pymem.py browse -t stdlib      # study sheet: every card with its answer
python pymem.py reset                 # start over
python pymem.py selftest              # verify every card in the bank works
```

Progress is saved in `~/.pymem_progress.json` (change it with `--data FILE` or `PYMEM_DATA`).

## Topics

`basics` · `strings` · `lists` · `dicts` · `control` · `comprehensions` · `functions` · `iterators` ·
`builtins` · `stdlib` · `oop` · `exceptions` · `decorators` · `idioms`

## Adding your own cards

Cards live in [`cards.py`](cards.py). Add one under the matching `topic(...)` line:

```python
output("list.my_trap", """
    a = [1, 2, 3]
    print(a[-1:], a[5:])
""", why="Slices clip instead of raising IndexError.")

expr("str.title", "Capitalize each word of `s`.", 's = "hello world"', "s.title()",
     alt=['s = "a b"'])

code("func.clamp", "Write `clamp(x, lo, hi)`.", """
    def clamp(x, lo, hi):
        return max(lo, min(x, hi))
""", tests=["clamp(5, 0, 3) == 3", "clamp(-1, 0, 3) == 0"])
```

Then run `python pymem.py selftest`. It runs every snippet and checks that every reference answer passes its own tests.
