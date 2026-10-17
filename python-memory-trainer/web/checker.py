"""Answer checking for the web version, run inside Pyodide (in a Web Worker).

A port of check_expr / check_code from ../pymem.py without the signal-based
time limit: the page kills the worker when a check takes too long.
Called from py-worker.js through check_json(kind, card_json, answer).
"""

import ast
import collections.abc
import contextlib
import io
import json


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


def execute(source, ns, mode="exec"):
    """Run source in namespace ns. Returns (value, captured stdout, exception or None)."""
    buf = io.StringIO()
    value = error = None
    with contextlib.redirect_stdout(buf):
        try:
            compiled = compile(source, "<your code>", mode)
            value = eval(compiled, ns) if mode == "eval" else exec(compiled, ns)
        except BaseException as err:  # user code may raise anything, even SystemExit
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


def reference_value(card, setup):
    ns = new_namespace()
    execute(setup, ns)
    value, _, err = execute(card["answer"], ns, "eval")
    return value, err


def check_expr(card, user):
    try:
        compile(user, "<expr>", "eval")
    except SyntaxError as err:
        hint = " (I need an expression, not an assignment)" if "=" in user else ""
        return False, f"not a valid expression: {err.msg}{hint}"
    for n, setup in enumerate([card["code"]] + list(card["alt"])):
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
                           f"it gives {short_repr(got)} instead of {short_repr(want)}. No hard-coding 😉")
        if card["check"]:
            try:
                passed = eval(card["check"], {"result": got})
            except Exception:
                passed = False
            if not passed:
                return False, card["checkMsg"] or "close, but it fails an extra check"
    return True, ""


def actual_side(test, ns):
    """For a failing `left == right` test, show what `left` evaluated to."""
    try:
        node = ast.parse(test, mode="eval").body
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], (ast.Eq, ast.Is)):
            left = ast.get_source_segment(test, node.left)
            value, _, err = execute(left, ns, "eval")
            if err is None:
                return f"\n{left} gave {short_repr(value)}"
    except (SyntaxError, ValueError):
        pass
    return ""


def check_code(card, src):
    ns = new_namespace()
    ns["raises"] = raises
    printed = ""
    for label, source in (("setup", card["code"]), ("your code", src), ("test setup", card["after"])):
        if not source:
            continue
        _, out, err = execute(source, ns)
        printed += out
        if err is not None:
            if label == "your code":
                return False, f"your code raised {exc_text(err)}"
            return False, f"{label} failed: {exc_text(err)}"
    for test in card["tests"]:
        value, out, err = execute(test, ns, "eval")
        printed += out
        if err is not None:
            msg = f"{test}\nraised {exc_text(err)}"
        elif not value:
            msg = f"failed: {test}{actual_side(test, ns)}"
        else:
            continue
        if printed.strip():
            msg += "\nyour code printed: " + short_repr(printed.strip(), 200)
        return False, msg
    return True, ""


def check_json(kind, card_json, answer):
    card = json.loads(card_json)
    ok, msg = (check_expr if kind == "expr" else check_code)(card, answer)
    return json.dumps({"ok": ok, "msg": msg})
