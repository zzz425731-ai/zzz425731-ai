#!/usr/bin/env python3
"""Build the web (iPhone-friendly) version of PyMem into web/dist/.

    python web/build.py            # writes dist/: index.html, cards.js, py-worker.js, pyodide/

cards.js holds every card from ../cards.py plus things computed here with real
CPython: the expected output of each snippet, the target value of each one-liner,
and syntax-highlighted HTML for all code. Pyodide (Python compiled to
WebAssembly) is downloaded once from npm into dist/pyodide/; the page loads it
in a Web Worker to check one-liners and code answers.
"""

import html
import io
import re
import json
import keyword
import builtins
import shutil
import sys
import tarfile
import tokenize
import urllib.request
from pathlib import Path

WEB = Path(__file__).resolve().parent
ROOT = WEB.parent
DIST = WEB / "dist"
sys.path.insert(0, str(ROOT))

import pymem  # noqa: E402  (the CLI: reused for running snippets and reference answers)
from cards import CARDS, TOPICS  # noqa: E402

PYODIDE_VERSION = "0.27.7"
PYODIDE_FILES = ["pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"]
BUILTIN_NAMES = set(dir(builtins))
FSTRING_TOKENS = {getattr(tokenize, n) for n in ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END")
                  if hasattr(tokenize, n)}


def highlight_html(src):
    """Python source -> HTML with <span class="t-..."> tokens (same rules as pymem.highlight)."""
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
            cls = None
            if tok.type == tokenize.NAME:
                if keyword.iskeyword(tok.string):
                    cls = "kw"
                elif prev in ("def", "class"):
                    cls = "fn"
                elif tok.string in BUILTIN_NAMES:
                    cls = "bi"
            elif tok.type == tokenize.STRING or tok.type in FSTRING_TOKENS:
                cls = "str"
            elif tok.type == tokenize.NUMBER:
                cls = "num"
            elif tok.type == tokenize.COMMENT:
                cls = "com"
            out.append(html.escape(src[last:start]))
            text = html.escape(src[start:end])
            out.append(f'<span class="t-{cls}">{text}</span>' if cls else text)
            last = end
            if tok.type == tokenize.NAME:
                prev = tok.string
    except (tokenize.TokenError, SyntaxError):
        return html.escape(src)
    out.append(html.escape(src[last:]))
    return "".join(out)


def prose(text):
    """Undo the terminal's hard wrapping so text reflows on a phone.

    A line break stays when the next line is indented, a bullet or a label ("C++: ..."),
    or when the line itself is code (indented), a table row (aligned columns, "->") or ends with a colon.
    """
    lines = (text or "").split("\n")
    out = lines[:1]
    for line in lines[1:]:
        prev = out[-1]
        keep = (not line.strip() or line[:1].isspace() or re.match(r"[-*•]\s|\d+[.)]\s|[A-Z][\w+#]*( [\w+#]+)?:\s", line)
                or prev[:1].isspace() or "  " in prev.strip() or ("->" in prev and "->" in line) or prev.rstrip().endswith(":") or not prev.strip())
        if keep:
            out.append(line)
        else:
            out[-1] = prev.rstrip() + " " + line.lstrip()
    return "\n".join(out)


def prose_html(text):
    """Escaped prose with `backticks` turned into <code>."""
    return re.sub(r"`([^`\n]+)`", r"<code>\1</code>", html.escape(prose(text)))


def card_data(card):
    data = {
        "id": card.id, "topic": card.topic, "kind": card.kind, "q": card.q,
        "code": card.code, "answer": card.answer, "why": card.why,
        "qHtml": prose_html(card.q), "whyHtml": prose_html(card.why),
        "title": (prose(card.q) if card.q else card.code).split("\n")[0],
        "alt": list(card.alt), "tests": list(card.tests), "after": card.after,
        "check": card.check, "checkMsg": card.check_msg,
        "codeHtml": highlight_html(card.code) if card.code else "",
    }
    if card.kind == "concept":
        data["answerTextHtml"] = prose_html(card.answer)
    elif card.kind == "output":
        lines, err = pymem.snippet_output(card.code)
        data["out"], data["raises"] = lines, err is not None
    elif card.kind == "expr":
        value, err = pymem.reference_value(card, card.code)
        assert err is None, f"{card.id}: reference raised {err!r}"
        data["target"] = pymem.short_repr(value)
        data["answerHtml"] = highlight_html(card.answer)
    elif card.kind == "code":
        data["answerHtml"] = highlight_html(card.answer.rstrip("\n"))
    return data


STANDALONE_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>
</head>
<body>
"""


def fetch_pyodide():
    target = DIST / "pyodide"
    if all((target / name).exists() for name in PYODIDE_FILES):
        return
    target.mkdir(parents=True, exist_ok=True)
    url = f"https://registry.npmjs.org/pyodide/-/pyodide-{PYODIDE_VERSION}.tgz"
    print(f"downloading {url} ...")
    with urllib.request.urlopen(url) as resp:
        blob = resp.read()
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        for name in PYODIDE_FILES:
            member = tar.extractfile(f"package/{name}")
            (target / name).write_bytes(member.read())


def main():
    if pymem.cmd_selftest() != 0:
        sys.exit("selftest failed; fix the cards first")
    DIST.mkdir(exist_ok=True)
    cards = [card_data(c) for c in CARDS]
    payload = {
        "topics": [{"key": k, "title": t} for k, t in TOPICS.items()],
        "cards": cards,
        "checker": (WEB / "checker.py").read_text(encoding="utf-8"),
    }
    js = "// Generated by web/build.py from cards.py. Do not edit by hand.\n"
    js += "window.PYMEM_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (DIST / "cards.js").write_text(js, encoding="utf-8")
    # page.html is the page body as published to claude.ai (the host adds doctype/head);
    # index.html wraps the same body in a minimal document for hosting it yourself.
    page = (WEB / "index.html").read_text(encoding="utf-8")
    (DIST / "page.html").write_text(page, encoding="utf-8")
    (DIST / "index.html").write_text(STANDALONE_HEAD + page + "\n</body>\n</html>\n", encoding="utf-8")
    shutil.copy(WEB / "py-worker.js", DIST / "py-worker.js")
    fetch_pyodide()
    size = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
    print(f"built {DIST} ({len(cards)} cards, {size / 1e6:.1f} MB total)")


if __name__ == "__main__":
    main()
