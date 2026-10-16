"""Question bank for pymem.py.

Four kinds of cards:
  concept  recall an idea, then grade yourself
  output   predict what a snippet prints (checked by really running it)
  expr     write a one-line expression (checked against a reference expression)
  code     write a few lines or a function (checked with tests)

To add a card, call concept() / output() / expr() / code() under the right
topic() and run `python pymem.py selftest`. Card ids are stored in your progress
file, so don't rename an existing id.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass


@dataclass(frozen=True)
class Card:
    id: str
    topic: str
    kind: str          # "concept" | "output" | "expr" | "code"
    q: str = ""        # the question (output cards don't need one)
    code: str = ""     # output: the snippet · expr/code: setup shown to you
    answer: str = ""   # concept: answer · expr: reference expression · code: reference solution
    why: str = ""      # explanation shown after you answer
    alt: tuple = ()    # expr: extra setups your answer must also work for (no hard-coding)
    tests: tuple = ()  # code: expressions that must all be truthy
    after: str = ""    # code: runs after your code, before the tests
    check: str = ""    # expr: extra condition on `result` (your value)
    check_msg: str = ""
    min_py: tuple = (3, 8)


TOPICS = {}
CARDS = []
_topic = None


def topic(key, title):
    global _topic
    TOPICS[key] = title
    _topic = key


def _d(text):
    return textwrap.dedent(text).strip("\n")


def concept(id, q, a, why=""):
    CARDS.append(Card(id, _topic, "concept", q=_d(q), answer=_d(a), why=_d(why)))


def output(id, snippet, why="", min_py=(3, 8)):
    CARDS.append(Card(id, _topic, "output", code=_d(snippet), why=_d(why), min_py=min_py))


def expr(id, q, setup, answer, why="", alt=(), check="", check_msg=""):
    CARDS.append(Card(id, _topic, "expr", q=_d(q), code=_d(setup), answer=answer,
                      why=_d(why), alt=tuple(_d(a) for a in alt),
                      check=check, check_msg=check_msg))


def code(id, q, solution, tests, setup="", after="", why=""):
    CARDS.append(Card(id, _topic, "code", q=_d(q), code=_d(setup), answer=_d(solution) + "\n",
                      tests=tuple(tests), after=_d(after), why=_d(why)))


# ---------------------------------------------------------------------------
topic("basics", "Basics: types, operators, truthiness")

concept("basics.dynamic", """
    Python is "dynamically but strongly typed". What do the two halves mean?
""", """
    Dynamic: types belong to objects, not to variables. A name is just a label
    that can be re-bound to an object of any type at runtime.
    Strong: there are no implicit conversions between unrelated types,
    e.g. "1" + 1 raises TypeError instead of guessing.
""", why="""
    C++ is static (the compiler checks types) and has lots of implicit conversions.
    Python checks types at runtime and refuses to guess.
""")

output("basics.floordiv", """
    print(7 // 2, -7 // 2, -7 % 3, 7 / 2)
""", why="""
    // rounds toward minus infinity, and % takes the sign of the divisor,
    so (a // b) * b + a % b == a always holds. / always gives a float.
    C++: integer / truncates toward zero, so -7/2 == -3 and -7%3 == -1.
""")

output("basics.power_xor", """
    print(2 ** 10, 2 ^ 10, 10 ** 20 > 2 ** 63)
""", why="""
    ** is power and ^ is bitwise XOR (same as in C++): 0b0010 ^ 0b1010 == 0b1000.
    Python ints have arbitrary precision, so 10**20 just works. No overflow
    like with a 64-bit long long.
""")

output("basics.rounding", """
    print(round(2.5), round(3.5), int(3.9), int(-3.9))
""", why="""
    round() uses banker's rounding: halves go to the nearest EVEN number.
    int() truncates toward zero (it does not floor).
    Floats are IEEE-754 doubles like in C++: 0.1 + 0.2 != 0.3, so use math.isclose().
""")

output("basics.truthy", """
    for v in [0, "", "0", [], [0], None, " "]:
        print("T" if v else "F", end="")
    print()
""", why="""
    Falsy: None, False, 0, 0.0, and every EMPTY container ("", [], {}, set(), ...).
    Everything else is truthy, including "0", [0] and " ".
    Idiom: `if items:` instead of `if len(items) > 0:`.
""")

output("basics.is_vs_eq", """
    a = [1, 2, 3]
    b = a
    c = [1, 2, 3]
    print(a == c, a is c, a is b)
""", why="""
    == compares values (calls __eq__). `is` compares identity: same object?
    (Think of it as comparing pointers.) Use `is` only for None and sentinels:
    `if x is None:`.
""")

output("basics.chain_assign", """
    x = y = []
    x.append(1)
    a = b = 0
    a += 1
    print(y, b)
""", why="""
    `x = y = []` binds both names to the SAME list, so x.append shows up in y.
    Ints are immutable, so `a += 1` makes a new int and re-binds only a.
    Rule: names are references. Mutating is shared, re-binding is not.
""")

output("basics.short_circuit", """
    print(0 or "default", 3 and 4, None or [] or "last")
    print(repr("" and 1 / 0))
""", why="""
    `and`/`or` return one of their OPERANDS, not True/False.
    `x or y` gives the first truthy value (or the last one); `x and y` gives the
    first falsy value (or the last one). The right side is skipped when it isn't
    needed, so 1/0 never runs. Idiom: `name = user_input or "anonymous"`.
""")

output("basics.conversions", """
    print(int("42") + 1, str(42) + "1", int("ff", 16), float("1e3"))
    age = 30
    print("Age: " + age)
""", why="""
    Converting is always explicit: int(), str(), float(); int(s, base) parses
    other bases. Adding a str and an int raises TypeError.
    Use an f-string instead: f"Age: {age}".
""")

# ---------------------------------------------------------------------------
topic("strings", "Strings: slicing, methods, formatting")

output("str.slice", """
    s = "Python"
    print(s[0], s[-1], s[1:4], s[:2], s[::2], s[::-1])
""", why="""
    s[start:stop:step]: stop is excluded, negative indexes count from the end,
    and a missing start/stop means "from the edge". [::-1] reverses.
    Slices never raise IndexError. They just clip.
""")

expr("str.reverse", "Reverse the string `s`.", """
    s = "stressed"
""", "s[::-1]", alt=['s = "abc"'], why="""
    A step of -1 walks backwards. reversed(s) gives an iterator, so it would
    need "".join(reversed(s)).
""")

output("str.immutable", """
    s = "hello"
    t = "H" + s[1:]
    print(t)
    s[0] = "H"
""", why="""
    Strings are immutable: you can't assign to s[0]. Build a new string
    instead (slicing, replace, join...). Unlike std::string, which is mutable.
""")

output("str.ops", """
    print("ab" * 3, "-" * 5, "ell" in "hello", "Hello"[1:] + "!")
""", why="""
    * repeats, + concatenates, and `in` does a substring search.
    "-" * 40 is the classic way to draw a separator line.
""")

expr("str.join", "Join the strings in `words` with ', ' between them.", """
    words = ["red", "green", "blue"]
""", '", ".join(words)', alt=['words = ["solo"]', "words = []"], why="""
    join is a method of the SEPARATOR: sep.join(iterable_of_str).
    Building a string with += in a loop can be O(n^2); join is linear.
""")

output("str.split", """
    print("a,b,,c".split(","))
    print("  lots   of   space ".split())
""", why="""
    split(sep) keeps empty fields between separators.
    split() with no argument splits on runs of whitespace and drops the empties,
    which is almost always what you want for words.
""")

output("str.methods", """
    s = "  Hello, World!  "
    print(s.strip().lower(), s.count("l"), s.find("z"), s.strip().startswith("Hell"))
""", why="""
    String methods return NEW strings because strings are immutable.
    find() returns -1 when nothing is found; index() raises ValueError instead.
""")

output("str.fstring", """
    name, pi, n = "Ada", 3.14159, 42
    print(f"{name:>5}|{pi:.2f}|{n:05d}|{n:x}|{n=}")
""", why="""
    The format spec goes after the colon: >5 right-aligns to width 5, .2f gives
    2 decimals, 05d zero-pads, x is hex. {n=} (3.8+) prints "n=42", which is
    great for debugging. More specs: {x:,} for thousands, {x:.1%} for a percent.
""")

expr("str.count_vowels", "Count the vowels (a, e, i, o, u) in `text`.", """
    text = "programming in python"
""", 'sum(ch in "aeiou" for ch in text)', alt=['text = "xyz"', 'text = "banana"'], why="""
    True counts as 1, so sum(<bool generator>) counts the matches.
    This works for any "how many items satisfy X" question.
""")

output("str.repr", """
    words = ["hi", "there"]
    print(words, *words)
    print(str("hi"), repr("hi"), len(repr("hi")))
""", why="""
    str() is for humans; print uses it. repr() is for developers: unambiguous,
    and it includes quotes. Containers show the repr of their elements.
    *words unpacks the list into separate arguments.
""")

# ---------------------------------------------------------------------------
topic("lists", "Lists, mutability & copying")

output("list.append_extend", """
    a = [1, 2]
    a.append([3, 4])
    b = [1, 2]
    b.extend([3, 4])
    print(a, b, len(a), len(b))
""", why="""
    append adds ONE item (here, a whole list). extend adds each item of an
    iterable (like `b += [3, 4]`).
""")

output("list.alias", """
    a = [1, 2, 3]
    b = a
    b.append(4)
    c = a[:]
    c.append(5)
    print(a, c)
""", why="""
    Assignment never copies. b is just another name for the same list.
    a[:], list(a) and a.copy() make a (shallow) copy.
    C++ copies on `auto b = a;`. Python behaves more like `auto& b = a;`.
""")

output("list.iadd", """
    a = [1]
    b = a
    a += [2]
    a = a + [3]
    print(a, b)
""", why="""
    For lists, `a += x` mutates in place (like extend), so b sees the 2.
    `a = a + x` builds a NEW list and re-binds a, so b doesn't see the 3.
""")

output("list.grid_trap", """
    grid = [[0] * 3] * 3
    grid[0][0] = 1
    print(grid)
""", why="""
    `* 3` repeats the REFERENCE to the same inner list three times.
    Correct: [[0] * 3 for _ in range(3)], which makes a new list per row.
    ([0] * 3 itself is fine, because ints are immutable.)
""")

output("list.shallow", """
    import copy
    a = [[1, 2], [3]]
    b = a.copy()
    c = copy.deepcopy(a)
    a[0].append(99)
    print(b[0], c[0])
""", why="""
    A shallow copy makes a new outer list, but the inner lists are still shared.
    copy.deepcopy copies recursively.
""")

output("list.sort_vs_sorted", """
    nums = [3, 1, 2]
    result = nums.sort()
    print(result, nums, sorted("cab"))
""", why="""
    Methods that mutate (sort, append, reverse...) return None.
    sorted() returns a NEW list and accepts any iterable.
    Classic bug: nums = nums.sort() leaves nums as None.
""")

output("list.slice_assign", """
    a = [0, 1, 2, 3, 4, 5]
    a[1:3] = ["x"]
    del a[-1]
    print(a, a[::-2])
""", why="""
    Assigning to a slice can change the list's length. del removes by index or
    slice. A negative step walks backwards from the end.
""")

expr("list.last_n", "Get the last 3 items of `items` (as a list).", """
    items = [10, 20, 30, 40, 50]
""", "items[-3:]", alt=["items = [1, 2]"], why="""
    Negative start = count from the end. If the list is shorter, the slice just
    returns what's there, with no error.
""")

output("list.pop_insert", """
    stack = [1, 2, 3]
    print(stack.pop(), stack.pop(0), stack)
    stack.insert(0, "a")
    print(stack, stack.index(2))
""", why="""
    A list is a dynamic array (like std::vector): append and pop() at the end
    are O(1), but pop(0) and insert(0, x) are O(n). For a queue, use
    collections.deque.
""")

concept("list.complexity", """
    Big-O of: `x in list`, `x in set`, `d[key]`, `list.append`, `list.pop(0)`?
""", """
    x in list   -> O(n)  (linear scan)
    x in set    -> O(1) average (hash table)
    d[key]      -> O(1) average
    list.append -> O(1) amortized
    list.pop(0) -> O(n)  (shifts everything)
""", why="""
    If you test membership in a loop, convert to a set first:
    seen = set(items). This is the most common Python speed-up.
""")

# ---------------------------------------------------------------------------
topic("dicts", "Dicts & sets")

output("dict.get", """
    ages = {"ann": 31, "bob": 25}
    print(ages.get("cat"), ages.get("cat", 0), "ann" in ages, 31 in ages)
    print(ages["cat"])
""", why="""
    `in` checks KEYS. d.get(k, default) never raises; d[k] raises KeyError.
    C++: std::map::operator[] silently inserts a default. Python doesn't.
""")

output("dict.order", """
    d = {"b": 1, "a": 2}
    d["c"] = 3
    d["b"] = 4
    print(list(d), list(d.values()))
""", why="""
    Dicts remember insertion order (guaranteed since 3.7). Updating an existing
    key keeps its original position. It's not sorted like std::map.
""")

expr("dict.invert", "Swap the keys and values of `d` (dict comprehension).", """
    d = {"a": 1, "b": 2}
""", "{v: k for k, v in d.items()}", alt=['d = {"x": "y"}', "d = {}"], why="""
    .items() yields (key, value) pairs, which you unpack directly in the `for`.
""")

expr("dict.max_key", "Get the key in `scores` with the highest value.", """
    scores = {"ann": 72, "bob": 95, "cat": 88}
""", "max(scores, key=scores.get)", alt=['scores = {"solo": 1}', 'scores = {"a": 1, "b": 2}'], why="""
    Iterating a dict gives its keys, and key=scores.get ranks each key by its value.
    Same trick: sorted(scores, key=scores.get, reverse=True).
""")

code("dict.word_count", """
    Write `count_words(text)` that returns a dict mapping each word to how many
    times it appears. Words are separated by whitespace. No imports.
""", """
    def count_words(text):
        counts = {}
        for word in text.split():
            counts[word] = counts.get(word, 0) + 1
        return counts
""", tests=[
    'count_words("the cat and the hat") == {"the": 2, "cat": 1, "and": 1, "hat": 1}',
    'count_words("") == {}',
    'count_words("a  a   a") == {"a": 3}',
], why="""
    counts.get(word, 0) + 1 is the classic counting idiom.
    The one-liner version: collections.Counter(text.split()).
""")

output("dict.merge", """
    a = {"x": 1, "y": 2}
    b = {"y": 20, "z": 30}
    print({**a, **b})
    print(a | b == {**a, **b})
""", min_py=(3, 9), why="""
    When merging, later keys win. {**a, **b} works everywhere; a | b is 3.9+,
    and a |= b updates a in place (same as a.update(b)).
""")

output("dict.modify_while_iterating", """
    d = {"a": 1, "b": 2}
    for k in d:
        if d[k] == 1:
            del d[k]
""", why="""
    You can't change a dict's size while iterating over it.
    Loop over a snapshot, `for k in list(d):`, or build a new dict:
    {k: v for k, v in d.items() if v != 1}.
""")

output("dict.unhashable", """
    d = {}
    d[(1, 2)] = "tuple key"
    d[[1, 2]] = "list key"
""", why="""
    Dict keys and set members must be hashable. Immutable built-ins (int, str,
    tuple of hashables, frozenset) are; lists, dicts and sets are not.
""")

output("set.ops", """
    a = {1, 2, 3, 4}
    b = {3, 4, 5}
    print(a & b, a | b, a - b, a ^ b)
""", why="""
    & intersection, | union, - difference, ^ symmetric difference
    (in exactly one). Sets are unordered, so don't rely on the print order.
""")

output("set.empty", """
    x = {}
    y = set()
    print(type(x).__name__, type(y).__name__, len({1, 1, 2, 2}))
""", why="""
    {} is an empty DICT. The empty set has to be written set().
    Sets drop duplicates, so list(set(xs)) dedupes (but loses order).
""")

# ---------------------------------------------------------------------------
topic("control", "Control flow & looping")

output("ctrl.range", """
    print(list(range(5)), list(range(2, 10, 3)), list(range(5, 0, -2)))
""", why="""
    range(start, stop, step), with stop excluded, like a C++ `for (i = a; i < b; i += s)`.
    range is lazy, so range(10**9) costs no memory.
""")

expr("ctrl.enumerate", "Build a list of (index, item) pairs for `items`, with the index starting at 1.", """
    items = ["a", "b"]
""", "list(enumerate(items, start=1))", alt=['items = ["x"]', "items = []"], why="""
    Use `for i, x in enumerate(xs):` instead of `for i in range(len(xs)):`.
    start= picks the first index.
""")

output("ctrl.zip", """
    names = ["ann", "bob", "cat"]
    ages = [31, 25]
    for name, age in zip(names, ages):
        print(name, age)
""", why="""
    zip walks several iterables in parallel and STOPS AT THE SHORTEST.
    Use zip(..., strict=True) (3.10+) to get an error instead, or
    itertools.zip_longest to pad.
""")

output("ctrl.for_else", """
    for n in [3, 5, 7]:
        if n % 2 == 0:
            print("found even", n)
            break
    else:
        print("no even numbers")
""", why="""
    A loop's `else` runs when the loop finishes WITHOUT hitting break.
    It replaces the C++ `bool found = false;` flag pattern in search loops.
""")

output("ctrl.scope_leak", """
    for i in range(3):
        pass
    print(i)
    squares = [j * j for j in range(3)]
    print("j" in globals())
""", why="""
    Python has no block scope: if/for/while do NOT create a new scope, so the
    loop variable i is still alive afterwards (C++ would say it's out of scope).
    Comprehensions do have their own scope, so j doesn't leak.
""")

output("ctrl.walrus", """
    data = [1, 0, 3, 4]
    while (n := data.pop()) != 0:
        print(n, end=" ")
    print("| left:", data)
""", why="""
    := (the "walrus", 3.8+) assigns inside an expression, like C++'s
    `while ((n = next()) != 0)`. end=" " stops print from adding a newline.
""")

output("ctrl.ternary", """
    n = 7
    parity = "even" if n % 2 == 0 else "odd"
    print(parity, "big" if n > 5 else "small")
""", why="""
    Python's ternary is `A if cond else B` (C++: cond ? A : B).
""")

output("ctrl.modify_while_iterating", """
    nums = [1, 2, 2, 3]
    for n in nums:
        if n == 2:
            nums.remove(n)
    print(nums)
""", why="""
    Removing items while iterating shifts everything left, so the loop SKIPS
    the next element (the second 2 is never checked). Build a new list instead:
    nums = [n for n in nums if n != 2].
""")

output("ctrl.match", """
    def describe(point):
        match point:
            case (0, 0):
                return "origin"
            case (0, y):
                return f"on y-axis at {y}"
            case (x, 0):
                return f"on x-axis at {x}"
            case _:
                return "somewhere else"

    print(describe((0, 0)), describe((0, 5)), describe((3, 4)), sep=" | ")
""", min_py=(3, 10), why="""
    match/case (3.10+) is structural pattern matching: it DESTRUCTURES values
    and binds names (y, x), not just compares constants like C++ switch.
    _ is the wildcard. sep= changes what print puts between its arguments.
""")

code("ctrl.fizzbuzz", """
    Write `fizzbuzz(n)` returning a list of strings for 1..n: "Fizz" for
    multiples of 3, "Buzz" for multiples of 5, "FizzBuzz" for both, otherwise
    the number as a string.
""", """
    def fizzbuzz(n):
        out = []
        for i in range(1, n + 1):
            word = ("Fizz" if i % 3 == 0 else "") + ("Buzz" if i % 5 == 0 else "")
            out.append(word or str(i))
        return out
""", tests=[
    'fizzbuzz(5) == ["1", "2", "Fizz", "4", "Buzz"]',
    'fizzbuzz(15)[-1] == "FizzBuzz"',
    "fizzbuzz(0) == []",
], why="""
    `word or str(i)` uses the fact that "" is falsy.
    Remember range(1, n + 1), since the stop value is excluded.
""")

# ---------------------------------------------------------------------------
topic("comprehensions", "Comprehensions & generator expressions")

expr("comp.squares_even", "A list of the squares of the EVEN numbers in `nums`.", """
    nums = [1, 2, 3, 4, 5, 6]
""", "[n * n for n in nums if n % 2 == 0]", alt=["nums = []", "nums = [-2, 3]"], why="""
    The shape is [transform for item in iterable if filter], which reads like the
    C++ loop it replaces.
""")

output("comp.if_position", """
    nums = [1, 2, 3, 4]
    print([n if n % 2 else 0 for n in nums])
    print([n for n in nums if n % 2])
""", why="""
    An `if` AFTER the for is a filter (it drops items).
    `a if cond else b` BEFORE the for is a ternary (it transforms every item).
""")

expr("comp.flatten", "Flatten the 2-D list `matrix` into one flat list (one comprehension).", """
    matrix = [[1, 2], [3, 4], [5]]
""", "[x for row in matrix for x in row]", alt=["matrix = [[], [7]]"], why="""
    Multiple fors run in the same order as nested loops: outer first.
    Read it as: for row in matrix: for x in row: keep x.
""")

expr("comp.dict_len", "A dict mapping each word in `words` to its length.", """
    words = ["hi", "hello"]
""", "{w: len(w) for w in words}", alt=["words = []"], why="""
    Dict comprehension: {key_expr: value_expr for ...}.
""")

expr("comp.set_letters", "The SET of unique lowercase first letters of `names`.", """
    names = ["Ann", "alex", "Bob", "bea", "Cy"]
""", "{n[0].lower() for n in names}", alt=["names = []"], why="""
    Set comprehension: braces without a colon. Duplicates disappear.
""")

expr("comp.filter_dict", "Keep only the entries of `prices` whose value is under 10.", """
    prices = {"tea": 3, "cake": 12, "pie": 8}
""", "{k: v for k, v in prices.items() if v < 10}", alt=["prices = {}"], why="""
    Filtering a dict is a dict comprehension over .items() with an if.
""")

expr("comp.table", "An n x n multiplication table: result[i][j] == (i + 1) * (j + 1).", """
    n = 3
""", "[[(i + 1) * (j + 1) for j in range(n)] for i in range(n)]", alt=["n = 2", "n = 0"], why="""
    A comprehension INSIDE a comprehension builds a 2-D list where every row is
    a new list (unlike [[0] * n] * n).
""")

output("comp.genexp_once", """
    squares = (n * n for n in range(4))
    print(sum(squares), sum(squares))
""", why="""
    Parentheses give a generator expression: lazy and SINGLE-USE. The second
    sum gets an exhausted generator, so 0. Use a list if you need two passes.
    sum(x * x for x in nums) avoids building a temporary list.
""")

# ---------------------------------------------------------------------------
topic("functions", "Functions, scope & closures")

output("func.mutable_default", """
    def add_item(item, bucket=[]):
        bucket.append(item)
        return bucket

    print(add_item(1), add_item(2))
""", why="""
    Default values are evaluated ONCE, when `def` runs, and then shared by
    every call. Fix:
        def add_item(item, bucket=None):
            if bucket is None:
                bucket = []
""")

concept("func.signature", """
    In `def f(a, b=2, *args, c, d=4, **kwargs)`, what are `args`, `c` and `kwargs`?
""", """
    args   -> a TUPLE of extra positional arguments
    c      -> keyword-only (it comes after *args), so it must be passed as c=...
    kwargs -> a DICT of extra keyword arguments
""", why="""
    A bare `*` (def f(a, *, c)) makes c keyword-only without collecting extras.
    A `/` (def f(a, /, b)) makes a positional-only (3.8+).
""")

output("func.args_kwargs", """
    def f(a, *args, sep="-", **kwargs):
        print(a, args, sep, kwargs)

    f(1, 2, 3, sep="+", x=9)
    f(*[10, 20], **{"y": 1})
""", why="""
    In a def, * and ** COLLECT arguments; in a call, they UNPACK a sequence or
    dict into arguments. A 1-tuple prints as (20,), with the trailing comma.
""")

output("func.kwonly", """
    def connect(host, *, port=80):
        return f"{host}:{port}"

    print(connect("example.com", port=8080))
    print(connect("example.com", 8080))
""", why="""
    Everything after a bare * is keyword-only, which forces readable calls
    like connect(host, port=8080) and prevents mixing up arguments.
""")

output("func.legb", """
    x = "global"

    def outer():
        x = "enclosing"
        def inner():
            return x
        return inner()

    print(outer(), x)
""", why="""
    Name lookup order is LEGB: Local -> Enclosing function -> Global -> Builtins.
    The x inside outer is a new local and doesn't touch the global one.
""")

output("func.unbound_local", """
    count = 0

    def increment():
        count += 1

    increment()
""", why="""
    Assigning to a name ANYWHERE in a function makes it local for the WHOLE
    function, so `count += 1` reads a local that has no value yet.
    Fix: `global count` (or better, return the new value).
""")

output("func.closure_counter", """
    def make_counter():
        count = 0
        def step():
            nonlocal count
            count += 1
            return count
        return step

    c1, c2 = make_counter(), make_counter()
    print(c1(), c1(), c2())
""", why="""
    A closure remembers the variables of the scope it was created in.
    `nonlocal` lets it RE-BIND them. Each make_counter() call creates a fresh
    count, so c1 and c2 are independent.
""")

output("func.late_binding", """
    funcs = [lambda: i for i in range(3)]
    print([f() for f in funcs])
""", why="""
    Closures look up i when CALLED, not when created, and by then i == 2.
    Fix: lambda i=i: i (a default value is evaluated at creation time).
    C++ lambdas choose [=] or [&]; Python closures always behave like [&].
""")

code("func.make_multiplier", """
    Write `make_multiplier(n)` that returns a FUNCTION which multiplies its
    argument by n. Example: make_multiplier(3)(5) == 15.
""", """
    def make_multiplier(n):
        def multiply(x):
            return x * n
        return multiply
""", tests=[
    "make_multiplier(2)(21) == 42",
    "make_multiplier(0)(9) == 0",
    "make_multiplier(-1)(5) == -5",
], why="""
    A function factory: the inner function closes over n.
    The short version: return lambda x: x * n.
""")

output("func.return_none", """
    def greet(name):
        print("hi", name)

    result = greet("ann")
    print(result)
""", why="""
    A function without a return statement returns None. print() returns None too.
""")

output("func.tuple_return", """
    def min_max(nums):
        return min(nums), max(nums)

    lo, hi = min_max([4, 1, 9])
    both = min_max([2])
    print(lo, hi, both)
""", why="""
    `return a, b` returns ONE tuple, which you unpack at the call site.
    It's like returning a std::pair and using structured bindings.
""")

concept("func.first_class", """
    What does it mean that functions are "first-class objects" in Python?
    Give two practical uses.
""", """
    Functions are ordinary objects. You can assign them to names, store them in
    lists or dicts, pass them as arguments, and return them from other functions.
    Uses: key=len in sorted(), dispatch tables {"add": add, "sub": sub},
    callbacks, closures and decorators.
""")

# ---------------------------------------------------------------------------
topic("iterators", "Iterators & generators")

concept("iter.protocol", """
    What's the difference between an ITERABLE and an ITERATOR?
""", """
    Iterable: anything iter() works on (list, str, dict, range, file...). Its
    __iter__ returns a fresh iterator, so you can loop over it many times.
    Iterator: has __next__, produces items one at a time, raises StopIteration
    at the end, and is SINGLE-PASS (its __iter__ returns itself).
    A for loop does: it = iter(obj); then next(it) until StopIteration.
""")

output("iter.next", """
    it = iter([10, 20])
    print(next(it), next(it), next(it, "done"))
    print(next(it))
""", why="""
    next(it, default) returns the default when the iterator is exhausted;
    without a default you get StopIteration.
""")

output("iter.gen_lazy", """
    def countdown(n):
        print("start")
        while n > 0:
            yield n
            n -= 1

    gen = countdown(3)
    print("created")
    print(list(gen))
""", why="""
    Calling a generator function runs NONE of its body. It only creates a
    generator object. The body runs bit by bit as next() is called, pausing at
    each yield.
""")

code("iter.fib", """
    Write a generator `fib()` that yields the Fibonacci numbers forever:
    0, 1, 1, 2, 3, 5, 8, ...
""", """
    def fib():
        a, b = 0, 1
        while True:
            yield a
            a, b = b, a + b
""", setup="from itertools import islice", tests=[
    "list(islice(fib(), 8)) == [0, 1, 1, 2, 3, 5, 8, 13]",
    "next(fib()) == 0",
], why="""
    Infinite generators are fine because they're lazy. Take what you need with
    itertools.islice. a, b = b, a + b updates both at once with no temp variable.
""")

code("iter.chunks", """
    Write a generator `chunks(seq, n)` that yields successive lists of n items
    (the last one may be shorter).  chunks([1, 2, 3, 4, 5], 2) -> [1, 2], [3, 4], [5]
""", """
    def chunks(seq, n):
        for i in range(0, len(seq), n):
            yield list(seq[i:i + n])
""", tests=[
    "list(chunks([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]",
    "list(chunks([], 3)) == []",
    "list(chunks([1, 2, 3], 3)) == [[1, 2, 3]]",
    'hasattr(chunks([1], 1), "__next__")',
], why="""
    range(0, len(seq), n) steps through the start indexes, and slicing clips at
    the end. (3.12+ has this built in: itertools.batched.)
""")

output("iter.yield_from", """
    def chain(*iterables):
        for it in iterables:
            yield from it

    print(list(chain("ab", [1, 2], range(2))))
""", why="""
    `yield from it` yields every item of `it`. It's short for
    `for x in it: yield x`. The standard library version is itertools.chain.
""")

output("iter.map_once", """
    m = map(str.upper, ["a", "b"])
    print(list(m), list(m))
""", why="""
    In Python 3, map, filter, zip and enumerate return lazy, one-shot iterators.
    Once consumed, they're empty.
""")

output("iter.dict_iter", """
    d = {"x": 1, "y": 2}
    for k in d:
        print(k, end=" ")
    for k, v in d.items():
        print(f"{k}={v}", end=" ")
    print()
""", why="""
    Iterating a dict yields its KEYS. Use .items() for (key, value) pairs and
    .values() for the values.
""")

concept("iter.when_generator", """
    When should you use a generator instead of building a list?
""", """
    When you only need ONE pass over the data, when the data is huge or
    infinite, or when you want to stream it (files, pipelines). A generator
    keeps O(1) memory.
    Use a list when you need len(), indexing, or several passes.
""")

# ---------------------------------------------------------------------------
topic("builtins", "Built-in functions")

expr("bi.sort_age", "Sort `people` (name, age) tuples by age, youngest first.", """
    people = [("ann", 31), ("bob", 25), ("cat", 40)]
""", "sorted(people, key=lambda p: p[1])", alt=['people = [("x", 2), ("y", 1)]'], why="""
    key= maps each item to the value to sort by. sorted is stable, so items with
    equal keys keep their order. operator.itemgetter(1) also works.
""")

expr("bi.sort_multi", "Sort `words` by length, then alphabetically within the same length.", """
    words = ["pear", "fig", "apple", "kiwi"]
""", "sorted(words, key=lambda w: (len(w), w))", alt=['words = ["bb", "a", "ab"]'], why="""
    Tuples compare item by item, so a tuple key sorts by several criteria.
    Mixed directions for numbers: key=lambda w: (-len(w), w).
""")

expr("bi.max_len", "The longest string in `words`.", """
    words = ["kiwi", "banana", "fig"]
""", "max(words, key=len)", alt=['words = ["xx", "y"]'], why="""
    min and max take key= just like sorted. They return the item itself, not the
    key value.
""")

expr("bi.any_negative", "True if ANY number in `nums` is negative.", """
    nums = [3, 0, -1, 5]
""", "any(n < 0 for n in nums)", alt=["nums = [1, 2]", "nums = []"], why="""
    any() and all() take a generator and short-circuit, stopping at the first
    decisive item.
""")

output("bi.all_any_empty", """
    print(all([]), any([]), all([1, "a", [0]]), any([0, "", None]))
""", why="""
    all([]) is True (nothing is false: "vacuous truth"), and any([]) is False.
    [0] is a non-empty list, so it's truthy even though it contains 0.
""")

output("bi.zip_dict", """
    keys = ["a", "b", "c"]
    values = [1, 2, 3]
    print(dict(zip(keys, values)))
    print(list(zip(*[(1, "x"), (2, "y")])))
""", why="""
    dict(zip(keys, values)) builds a dict from two parallel lists.
    zip(*pairs) "unzips" (transposes) a list of pairs.
""")

output("bi.math", """
    print(divmod(17, 5), abs(-3), pow(2, 10, 1000), round(3.14159, 2))
""", why="""
    divmod gives (quotient, remainder) in one go. pow(base, exp, mod) does fast
    modular exponentiation, which is handy for competitive programming.
""")

output("bi.isinstance", """
    print(isinstance(True, int), isinstance(3, (int, float)), type(3) == float)
""", why="""
    bool is a subclass of int (True == 1). isinstance respects inheritance and
    accepts a tuple of types, so prefer it over type(x) == ...
""")

output("bi.reversed", """
    nums = [3, 1, 2]
    print(sorted(nums, reverse=True), list(reversed(nums)), nums)
""", why="""
    reversed() gives a lazy iterator over the list backwards. Neither
    sorted() nor reversed() modifies the original list.
""")

expr("bi.digits", "Convert the all-digit strings in `tokens` to ints, skipping the others.", """
    tokens = ["12", "x", "7", "3a"]
""", "[int(t) for t in tokens if t.isdigit()]", alt=["tokens = []", 'tokens = ["0", "00"]'], why="""
    A filter plus a transform in one comprehension. This is usually clearer than
    list(map(int, filter(str.isdigit, tokens))).
""")

output("bi.chr_ord", """
    print(ord("a"), chr(ord("a") + 2), bin(10), hex(255), int("1010", 2))
""", why="""
    ord() gives a character's code point and chr() goes back. bin/hex/oct give
    strings, and int(s, base) parses them.
""")

# ---------------------------------------------------------------------------
topic("stdlib", "Standard library power tools")

concept("std.which", """
    Which standard-library tool do you reach for when you need:
    counting, grouping into lists, a FIFO queue, a priority queue,
    a small immutable record, a sorted-list search?
""", """
    counting        -> collections.Counter
    grouping        -> collections.defaultdict(list)
    FIFO queue      -> collections.deque (append / popleft)
    priority queue  -> heapq (a min-heap on a plain list)
    record          -> collections.namedtuple or @dataclass(frozen=True)
    binary search   -> bisect (bisect_left / bisect_right)
""")

expr("std.counter", "The 2 most common letters in `word`, as (letter, count) pairs.", """
    from collections import Counter
    word = "mississippi"
""", "Counter(word).most_common(2)", alt=['from collections import Counter\nword = "banana"'], why="""
    Counter is a dict subclass for counting. most_common(n) is sorted by count,
    and ties keep first-seen order. Counters can even be added and subtracted.
""")

code("std.group_by_len", """
    Write `group_by_len(words)` returning a dict {length: [words of that length]}
    that keeps the original order. Use collections.defaultdict.
""", """
    def group_by_len(words):
        groups = defaultdict(list)
        for w in words:
            groups[len(w)].append(w)
        return dict(groups)
""", setup="from collections import defaultdict", tests=[
    'group_by_len(["hi", "yo", "hey", "a"]) == {2: ["hi", "yo"], 3: ["hey"], 1: ["a"]}',
    "group_by_len([]) == {}",
], why="""
    defaultdict(list) creates an empty list the first time a key is used.
    Without it: groups.setdefault(len(w), []).append(w).
""")

output("std.deque", """
    from collections import deque
    q = deque([1, 2, 3], maxlen=3)
    q.append(4)
    print(q)
    q.appendleft(0)
    print(q.popleft(), list(q))
""", why="""
    deque is O(1) at BOTH ends (like std::deque). With maxlen it becomes a
    bounded buffer: adding on one side drops items from the other side.
""")

output("std.namedtuple", """
    from collections import namedtuple
    Point = namedtuple("Point", "x y")
    p = Point(3, 4)
    print(p, p.x + p[1])
    print(p._replace(x=0))
""", why="""
    A namedtuple is a tuple with field names: immutable, unpackable, and it has
    a nice repr. _replace returns a modified COPY.
""")

output("std.lru_cache", """
    from functools import lru_cache

    calls = 0

    @lru_cache(maxsize=None)
    def fib(n):
        global calls
        calls += 1
        return n if n < 2 else fib(n - 1) + fib(n - 2)

    print(fib(10), calls)
""", why="""
    Memoization by decorator: each fib(k) runs once (k = 0..10, so 11 calls).
    Without the cache it's 177 calls. Exponential becomes linear.
    functools.cache (3.9+) is the same as lru_cache(maxsize=None).
""")

output("std.itertools", """
    from itertools import product, permutations, combinations
    print(list(product("ab", repeat=2)))
    print(len(list(permutations(range(4), 2))), len(list(combinations(range(4), 2))))
""", why="""
    product = nested loops, permutations = order matters (4*3 = 12),
    combinations = order doesn't matter (4C2 = 6). It replaces hand-written
    nested loops and std::next_permutation.
""")

output("std.accumulate", """
    from itertools import accumulate, chain
    print(list(accumulate([1, 2, 3, 4])))
    print(list(chain([1], (2, 3), "ab")))
""", why="""
    accumulate gives running totals (prefix sums, like std::partial_sum).
    chain glues iterables together lazily.
""")

output("std.heapq", """
    import heapq
    h = []
    for x in [5, 1, 4, 2]:
        heapq.heappush(h, x)
    print(heapq.heappop(h), heapq.heappop(h), h[0])
""", why="""
    heapq is a MIN-heap on a plain list, so h[0] is always the smallest.
    (C++ priority_queue is a MAX-heap by default.) For a max-heap, push -x.
""")

expr("std.nsmallest", "The 3 smallest numbers in `nums`, ascending.", """
    import heapq
    nums = [7, 2, 9, 4, 1, 8]
""", "heapq.nsmallest(3, nums)", alt=["import heapq\nnums = [5, 5]"], why="""
    heapq.nsmallest/nlargest are O(n log k). sorted(nums)[:3] is also fine for
    small data.
""")

output("std.bisect", """
    import bisect
    a = [1, 3, 3, 7]
    print(bisect.bisect_left(a, 3), bisect.bisect_right(a, 3), bisect.bisect_left(a, 5))
""", why="""
    Binary search on a sorted list: bisect_left is C++ lower_bound and
    bisect_right is upper_bound. bisect.insort inserts and keeps the list sorted.
""")

# ---------------------------------------------------------------------------
topic("oop", "Classes & OOP")

concept("oop.self", """
    Why does every instance method take `self`? What does obj.method(x) really do?
""", """
    obj.method(x) is sugar for Class.method(obj, x), so self is the instance
    passed in explicitly, Python's version of C++'s implicit `this`.
    There's no implicit member access: you must write self.attr, otherwise it's
    just a local variable.
""")

output("oop.class_attr", """
    class Dog:
        tricks = []

        def __init__(self, name):
            self.name = name

        def add_trick(self, trick):
            self.tricks.append(trick)

    a, b = Dog("rex"), Dog("fido")
    a.add_trick("roll")
    print(b.tricks)
""", why="""
    Attributes in the class body are CLASS attributes, shared by all instances
    (like static members). Per-instance state belongs in __init__:
    self.tricks = [].
""")

output("oop.repr_str", """
    class Point:
        def __init__(self, x, y):
            self.x, self.y = x, y

        def __repr__(self):
            return f"Point({self.x}, {self.y})"

        def __str__(self):
            return f"({self.x}, {self.y})"

    p = Point(1, 2)
    print(p, [p], f"{p!r}")
""", why="""
    print and str() use __str__; containers, the REPL and !r use __repr__.
    If you write only one, write __repr__, because str() falls back to it.
""")

output("oop.eq_default", """
    class P:
        def __init__(self, x):
            self.x = x

    print(P(1) == P(1), P(1) != P(1))
""", why="""
    Without __eq__, == compares IDENTITY (like `is`). Define __eq__, or use
    @dataclass, which writes it for you. != automatically uses the inverse of
    __eq__.
""")

code("oop.vector", """
    Write a class `Vec` with __init__(self, x, y), __add__ (returns a NEW Vec),
    __eq__ (compare x and y), and __abs__ (the length: sqrt(x^2 + y^2)).
""", """
    class Vec:
        def __init__(self, x, y):
            self.x, self.y = x, y

        def __add__(self, other):
            return Vec(self.x + other.x, self.y + other.y)

        def __eq__(self, other):
            return (self.x, self.y) == (other.x, other.y)

        def __abs__(self):
            return (self.x ** 2 + self.y ** 2) ** 0.5
""", tests=[
    "Vec(1, 2) + Vec(3, 4) == Vec(4, 6)",
    "Vec(1, 2) != Vec(2, 1)",
    "abs(Vec(3, 4)) == 5",
], why="""
    Operator overloading = "dunder" (double underscore) methods: __add__ is
    operator+, __eq__ is operator==, __lt__ is <, __len__ is len(), __getitem__
    is [], and so on. math.hypot(x, y) also computes the length.
""")

output("oop.property", """
    class Temp:
        def __init__(self, celsius):
            self.celsius = celsius

        @property
        def fahrenheit(self):
            return self.celsius * 9 / 5 + 32

    t = Temp(100)
    print(t.fahrenheit)
    t.fahrenheit = 0
""", why="""
    @property makes a method look like an attribute: it's computed, and
    read-only unless you add a @fahrenheit.setter. Start with plain attributes
    and switch to a property later without changing any callers. No Java/C++
    style getX()/setX() needed.
""")

output("oop.classmethod", """
    class Pizza:
        count = 0

        def __init__(self, toppings):
            self.toppings = toppings
            Pizza.count += 1

        @classmethod
        def margherita(cls):
            return cls(["tomato", "mozzarella"])

        @staticmethod
        def is_vegan(topping):
            return topping not in {"mozzarella", "ham"}

    p = Pizza.margherita()
    print(p.toppings, Pizza.count, Pizza.is_vegan("tomato"))
""", why="""
    @classmethod receives the class (cls), which makes it perfect for
    alternative constructors that also work for subclasses. @staticmethod gets
    neither self nor cls; it's just a function that lives in the class namespace.
""")

output("oop.inheritance", """
    class Animal:
        def __init__(self, name):
            self.name = name

        def speak(self):
            return "..."

    class Dog(Animal):
        def __init__(self, name, breed):
            super().__init__(name)
            self.breed = breed

        def speak(self):
            return "Woof"

    d = Dog("rex", "lab")
    print(d.name, d.speak(), isinstance(d, Animal), Dog.__mro__[1].__name__)
""", why="""
    Every method is "virtual": lookup follows the MRO (method resolution order)
    at runtime. super().__init__ runs the parent's initializer. Forget it, and
    self.name never gets set.
""")

code("oop.dataclass", """
    Using @dataclass, define `Item` with fields name: str, price: float and
    qty: int = 1, plus a method total() returning price * qty.
""", """
    @dataclass
    class Item:
        name: str
        price: float
        qty: int = 1

        def total(self):
            return self.price * self.qty
""", setup="from dataclasses import dataclass", tests=[
    'Item("pen", 1.5, 4).total() == 6.0',
    'Item("cup", 3.0).qty == 1',
    'Item("a", 1.0) == Item("a", 1.0)',
    'repr(Item("a", 1.0, 2)) == "Item(name=\'a\', price=1.0, qty=2)"',
], why="""
    @dataclass generates __init__, __repr__ and __eq__ from the annotated fields.
    frozen=True makes it immutable and hashable, and order=True adds < > etc.
    It's the go-to choice for plain data classes.
""")

concept("oop.private", """
    How does Python mark "private" attributes? Is it enforced?
""", """
    By convention only: _name means "internal, don't touch" (not enforced).
    __name (two leading underscores) triggers name mangling to _ClassName__name,
    which mainly avoids clashes in subclasses.
    There's no real private/protected like in C++. "We're all consenting adults."
""")

# ---------------------------------------------------------------------------
topic("exceptions", "Exceptions")

output("exc.flow", """
    def parse(s):
        try:
            n = int(s)
        except ValueError:
            print("bad:", s)
            return None
        else:
            print("ok:", n)
            return n
        finally:
            print("cleanup")

    parse("42")
    parse("x")
""", why="""
    try -> except (on error) / else (only if NO error) -> finally (ALWAYS,
    even after a return). Keep the try block small, and put the rest in else.
""")

output("exc.order", """
    try:
        [1, 2][5]
    except LookupError as e:
        print("lookup:", type(e).__name__)
    except IndexError:
        print("index")
""", why="""
    except clauses are checked top to bottom, and the FIRST match wins.
    IndexError (and KeyError) are subclasses of LookupError, so put the
    specific handlers first.
""")

output("exc.multiple", """
    for value in ["3", "x", None]:
        try:
            print(int(value))
        except (ValueError, TypeError) as e:
            print(type(e).__name__)
""", why="""
    Catch several types with a tuple. A bad string gives ValueError; a wrong
    type (None) gives TypeError. Avoid a bare `except:`, because it even swallows
    Ctrl+C.
""")

concept("exc.eafp", """
    What are EAFP and LBYL? Which one is more "Pythonic"?
""", """
    LBYL = Look Before You Leap:    if key in d: value = d[key]
    EAFP = Easier to Ask Forgiveness than Permission:
           try: value = d[key]
           except KeyError: ...
    EAFP is idiomatic Python. It's clean, and it avoids race conditions
    (e.g. a file deleted between the check and the open).
""")

code("exc.safe_div", """
    Write `safe_div(a, b)` returning a / b, or None if b is zero.
    Use try/except, not an if.
""", """
    def safe_div(a, b):
        try:
            return a / b
        except ZeroDivisionError:
            return None
""", tests=[
    "safe_div(6, 3) == 2",
    "safe_div(1, 0) is None",
    "safe_div(0, 5) == 0",
], why="""
    Catch the most SPECIFIC exception you expect (ZeroDivisionError), never a
    blanket except.
""")

code("exc.custom", """
    Define an exception class `InsufficientFunds` (a subclass of Exception), and
    `withdraw(balance, amount)` that returns the new balance, or raises
    InsufficientFunds if amount > balance.
""", """
    class InsufficientFunds(Exception):
        pass

    def withdraw(balance, amount):
        if amount > balance:
            raise InsufficientFunds(f"need {amount}, have {balance}")
        return balance - amount
""", tests=[
    "issubclass(InsufficientFunds, Exception)",
    "withdraw(10, 3) == 7",
    "withdraw(5, 5) == 0",
    "raises(InsufficientFunds, withdraw, 5, 10)",
], why="""
    A custom exception is a one-line class. Callers can catch exactly your
    error. Use `raise NewError(...) from err` to chain the original cause.
""")

# ---------------------------------------------------------------------------
topic("decorators", "Decorators & context managers")

output("deco.basic", """
    def shout(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs).upper() + "!"
        return wrapper

    @shout
    def greet(name):
        return f"hi {name}"

    print(greet("ann"), greet.__name__)
""", why="""
    @shout is sugar for greet = shout(greet): a decorator is a function that
    takes a function and returns a replacement. The name became "wrapper", so
    put @functools.wraps(func) on the wrapper to keep the name and docstring.
""")

code("deco.count_calls", """
    Write a decorator `count_calls` that counts calls to the decorated function
    in an attribute `.calls` (starting at 0), and keeps the original __name__
    (use functools.wraps).
""", """
    def count_calls(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wrapper.calls += 1
            return func(*args, **kwargs)
        wrapper.calls = 0
        return wrapper
""", setup="import functools", after="""
    @count_calls
    def hello(name):
        return "hi " + name
""", tests=[
    'hello("ann") == "hi ann"',
    "hello.calls == 1",
    'hello("b") and hello("c") and hello.calls == 3',
    'hello.__name__ == "hello"',
], why="""
    The pattern: def deco(func): @wraps(func) def wrapper(*args, **kwargs): ...
    return wrapper. Functions are objects, so they can carry attributes.
""")

output("deco.with_args", """
    def repeat(times):
        def decorator(func):
            def wrapper(*args):
                return [func(*args) for _ in range(times)]
            return wrapper
        return decorator

    @repeat(3)
    def roll():
        return 6

    print(roll())
""", why="""
    A decorator WITH arguments is a function that RETURNS a decorator, so three
    layers: repeat(3) -> decorator -> wrapper.
""")

output("ctx.enter_exit", """
    class Tag:
        def __init__(self, name):
            self.name = name

        def __enter__(self):
            print(f"<{self.name}>")
            return self

        def __exit__(self, exc_type, exc, tb):
            print(f"</{self.name}>")
            return False

    with Tag("b"):
        with Tag("i"):
            print("text")
""", why="""
    `with` calls __enter__ on the way in and __exit__ on the way out, ALWAYS,
    even on exceptions. It's Python's RAII (like a C++ destructor).
    If __exit__ returns True, the exception is swallowed.
""")

output("ctx.contextmanager", """
    from contextlib import contextmanager

    @contextmanager
    def opened(name):
        print("open", name)
        try:
            yield name.upper()
        finally:
            print("close", name)

    try:
        with opened("db") as handle:
            print("using", handle)
            raise RuntimeError("boom")
    except RuntimeError:
        print("handled")
""", why="""
    @contextmanager turns a generator into a context manager: the code before
    the yield is __enter__, the yielded value goes to `as`, and the code after it
    (in a finally) is __exit__. The cleanup still runs on errors.
""")

concept("ctx.open_file", r"""
    What's the idiomatic way to read a text file line by line, and why `with`?
""", r"""
    with open("data.txt", encoding="utf-8") as f:
        for line in f:
            handle(line.rstrip("\n"))

    `with` guarantees the file is closed even if an exception happens.
    Iterating the file object is lazy, so even huge files use little memory.
""")

# ---------------------------------------------------------------------------
topic("idioms", "Pythonic idioms")

concept("idiom.cpp_habits", """
    Name 3+ C++ habits to drop when writing Python.
""", """
    - for i in range(len(xs)): xs[i]   ->  for x in xs  /  for i, x in enumerate(xs)
    - swapping with a temp variable    ->  a, b = b, a
    - building strings with += in loops ->  "".join(parts)
    - flags/error codes                ->  exceptions, for-else, any()/all()
    - manual close()/cleanup           ->  with
    - if (x == true) / if (len(v) > 0) ->  if x: / if v:
""")

code("idiom.swap", "Swap the values of `a` and `b` in one line, with no temp variable.", """
    a, b = b, a
""", setup="a, b = 1, 2", tests=["(a, b) == (2, 1)"], why="""
    The right side builds a tuple (b, a) first, and then it's unpacked into a, b.
""")

output("idiom.star_unpack", """
    first, *middle, last = [1, 2, 3, 4, 5]
    head, *tail = "ab"
    print(first, middle, last, head, tail)
""", why="""
    A starred target collects "the rest", always as a LIST (even from a string).
""")

expr("idiom.transpose", "Transpose `matrix` into a list of tuples (hint: zip and *).", """
    matrix = [[1, 2, 3], [4, 5, 6]]
""", "list(zip(*matrix))", alt=["matrix = [[1], [2]]"], why="""
    *matrix passes each row as a separate argument, and zip pairs up their
    columns.
""")

expr("idiom.dict_from_lists", "Build a dict from the parallel lists `keys` and `values`.", """
    keys = ["a", "b", "c"]
    values = [1, 2, 3]
""", "dict(zip(keys, values))", alt=["keys = []\nvalues = []"], why="""
    zip pairs them up and dict() turns the pairs into entries.
""")

expr("idiom.dedupe", "Remove duplicates from `items`, keeping first-seen ORDER (one expression).", """
    items = [3, 1, 3, 2, 1]
""", "list(dict.fromkeys(items))", alt=['items = ["b", "a", "b"]'], why="""
    list(set(items)) loses the order. Dicts keep insertion order, and
    dict.fromkeys keeps only the first occurrence of each key.
""")

expr("idiom.palindrome", "True if `s` reads the same backwards, ignoring upper/lower case.", """
    s = "Racecar"
""", "s.lower() == s.lower()[::-1]", alt=['s = "Python"', 's = ""'], why="""
    Normalize first (lower()), then compare with the reversed slice.
""")

expr("idiom.grid", "A rows x cols grid of zeros where every row is an INDEPENDENT list.", """
    rows, cols = 3, 4
""", "[[0] * cols for _ in range(rows)]", alt=["rows, cols = 2, 2"],
    check="len(result) < 2 or result[0] is not result[1]",
    check_msg="the rows are all the SAME list object. [[0] * cols] * rows repeats one reference",
    why="""
    `_` is the conventional name for a loop variable you don't use.
    The comprehension builds a new inner list on every iteration.
""")

expr("idiom.nested_get", "Get config['db']['port'], or 5432 if 'db' or 'port' is missing (no try).", """
    config = {"db": {"host": "localhost"}}
""", 'config.get("db", {}).get("port", 5432)', alt=["config = {}", 'config = {"db": {"port": 3306}}'], why="""
    Chaining .get with an empty-dict default walks nested dicts safely.
""")

expr("idiom.sort_by_value", "The keys of `scores`, highest score first.", """
    scores = {"ann": 72, "bob": 95, "cat": 88}
""", "sorted(scores, key=scores.get, reverse=True)", alt=['scores = {"x": 1, "y": 2}'], why="""
    sorted(dict) sorts the keys, and key=scores.get ranks them by value.
""")

expr("idiom.join_numbers", "A comma-separated string of the numbers in `nums`, e.g. '1,2,3'.", """
    nums = [1, 2, 3]
""", '",".join(map(str, nums))', alt=["nums = []", "nums = [10]"], why="""
    join only accepts strings, so convert first with map(str, nums) or
    (str(n) for n in nums).
""")

expr("idiom.count_if", "How many numbers in `nums` are greater than 10?", """
    nums = [5, 12, 7, 30, 11]
""", "sum(n > 10 for n in nums)", alt=["nums = []"], why="""
    Summing booleans counts the Trues. len([n for n in nums if n > 10]) works
    too, but it builds a list.
""")

output("idiom.underscores", """
    for _ in range(2):
        print("hi", end=" ")
    total = 1_000_000
    print(total, f"{total:,}")
""", why="""
    `_` marks a throwaway variable. Underscores in number literals are just for
    readability. The `,` format spec adds thousands separators.
""")
