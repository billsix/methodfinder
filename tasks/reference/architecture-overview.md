# methodfinder — architecture overview

**Repo:** github.com/billsix/methodfinder
**What it is:** a tiny (single-module, ~390-line) Python library that answers the
question *"I know the inputs and the output, but I forget the name of the function that
connects them."* You hand it the argument(s) and the expected result, and it prints every
builtin, method, operator, or standard-library function it can find whose call produces
that result. It is a direct homage to the Smalltalk-80 "method finder" (see the very first
commit, `49acfdd "Initial implementation of a Smalltalk-80 like methodfinder"`).

**Audience:** interactive use at the Python REPL by a programmer who is stuck on a name.
It is a discovery aid, not something you call in production code.

## The one idea that makes it work

`methodfinder.find(...)` does **not** take the expected result as an argument. Instead
`find` returns a wrapper object (`_Foo`) whose `__eq__` is overloaded, so you write the
query as an expression that reads like an assertion:

```python
>>> import methodfinder
>>> methodfinder.find([1, 2, 3]) == 6
math.prod([1, 2, 3])
sum([1, 2, 3])
```

`find([1,2,3])` builds a `_Foo` holding the objects; the `== 6` then triggers the whole
search inside `_Foo.__eq__`, which **prints** the matches as a side effect and returns
`None` (never `True`/`False`). The `==` is syntactic sugar for "expected result", nothing
more. This DSL trick is the heart of the project; it is documented in detail in
[find-algorithm.md](find-algorithm.md).

## Top-level layout

```
methodfinder/
├── README.md                 # user-facing intro + a gallery of worked examples
├── LICENSE.txt               # MIT
├── pyproject.toml            # PEP 621 metadata (name, version 0.0.5, authors)
├── setup.cfg                 # setuptools src-layout + install_requires
├── setup.py                  # 4-line shim: setup() under __main__
├── .gitignore                # stock GitHub Python .gitignore
├── .githooks/pre-commit      # runs `black` on staged *.py, then a whitespace check
└── src/
    └── methodfinder/
        ├── __init__.py                 # `from .methodfinder import *`
        ├── methodfinder.py             # the entire implementation
        └── methodfinder-test.py        # unittest + doctest suite (note: hyphen in name)
```

There is exactly one real source file, `src/methodfinder/methodfinder.py`. Everything else
is packaging, one test file, and docs. There is no CLI, no network, no data files, no
build step beyond `pip install`.

## Entry points

- **Public API:** `methodfinder.find(*objects)` (`src/methodfinder/methodfinder.py:35`),
  re-exported via `src/methodfinder/__init__.py:1` (`from .methodfinder import *`). This is
  the only intended public name.
- **`_find(objects, expected_value)`** (`methodfinder.py:107`) is the un-sugared entry the
  tests call directly, bypassing the `_Foo`/`==` dance. It takes the expected value as a
  normal keyword argument and returns a sorted list of strings.

## Build / run / test

Requires Python 3.8+ (the enumerated results shift by Python version — see the caveat
below). `numpy` is needed only for the numpy examples in the tests and docstrings; it is
**not** declared as a dependency.

```sh
# install (editable), from the repo root
pip install -e .

# use it
python3 -c "import methodfinder; methodfinder.find([]) == 0"

# run the tests (the filename has a hyphen, so it is NOT importable as a module;
# run it directly, or with PYTHONPATH set so `import methodfinder` resolves):
cd src/methodfinder && PYTHONPATH=../ python3 methodfinder-test.py
```

`methodfinder-test.py` runs 16 tests: 15 hand-written `unittest` cases plus one
(`test_doctest`) that runs `doctest.testmod(methodfinder)` over the docstrings. See
[tests-and-packaging.md](tests-and-packaging.md) for details, including how the hyphenated
filename interacts with pytest/`-m unittest` discovery.

**Caveat — the expected-output listings drift with the Python version.** The *code* is
version-agnostic: it enumerates whatever `dir(builtins)`, `math`, etc. expose on the
running interpreter. But the expected outputs written into the README and the docstrings
are pinned to whatever Python the author last ran. On Python 3.14 the doctest
`find(0.0) == 1.0` fails because `math.exp2` (added in 3.11) is now a valid match that the
docstring doesn't list — the 15 non-doctest unit tests still pass. This is expected drift,
not a bug in the algorithm; details in
[tests-and-packaging.md](tests-and-packaging.md#python-version-drift).

## Reference-doc set

- **architecture-overview.md** (this file) — what methodfinder is, layout, entry points,
  build/run/test.
- **[find-algorithm.md](find-algorithm.md)** — the `find`/`_Foo.__eq__` DSL trick and the
  search algorithm: permutations, builtins sweep, attribute sweep, the nested/type-strict
  equality test, and how results are pretty-printed as operators vs method calls.
- **[tests-and-packaging.md](tests-and-packaging.md)** — the test suite, how it is run, the
  Python-version drift, and the packaging (`pyproject.toml`/`setup.cfg`/`setup.py`) and
  the `black` pre-commit hook.
