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
├── pyproject.toml            # PEP 621 metadata (version 0.0.5) + src-layout + ruff/ty config
├── setup.py                  # 4-line shim: setup() under __main__
├── .gitignore                # stock GitHub Python .gitignore
├── .githooks/pre-commit      # runs `ruff` on staged *.py, then a whitespace check
├── Dockerfile                # Fedora-44 image (python3/numpy/ruff/ty/uv); bakes source
├── Makefile                  # image/shell/shell-exec/format/type-check/test/image-{export,import}
├── entrypoint/               # container scripts (host-runnable)
│   ├── 01-install-base.sh     #   dnf install of the base packages
│   ├── shell.sh               #   venv + offline editable self-install, then `exec bash "$@"`
│   ├── format.sh              #   ruff check --fix + ruff format + ty
│   ├── type-check.sh          #   ty + check_local_annotations.py
│   ├── test.sh                #   runs the hyphenated test file directly
│   ├── entrypoint.sh          #   image ENTRYPOINT
│   └── dotfiles/.extrabashrc  #   format-on-shell-exit hook
├── tools/
│   ├── check_local_annotations.py  # vendored annotate-every-binding gate (canonical in runClaudeInContainer)
│   └── behavior_diff.py            # differential-output oracle for verifying refactors
└── src/
    └── methodfinder/
        ├── __init__.py                 # `from .methodfinder import find` (+ `__all__`)
        ├── methodfinder.py             # the entire implementation
        └── methodfinder-test.py        # unittest + doctest suite (note: hyphen in name)
```

There is exactly one real source file, `src/methodfinder/methodfinder.py`. Everything else
is packaging, one test file, the container template, and docs. The library has no CLI, no
network, no data files, and no third-party runtime dependencies; `pip install -e .` (or the
container's offline editable install) is the only build step for the package itself.
(`setup.cfg` was removed when the container was adopted 2026-11-02 — its src-layout wiring
moved into `pyproject.toml`'s `[tool.setuptools.packages.find]`, and its stale `mypy`
`install_requires` was dropped; the library needs no runtime deps.)

## Entry points

- **Public API:** `methodfinder.find(*objects)` (`src/methodfinder/methodfinder.py:33`),
  re-exported via `src/methodfinder/__init__.py` (`from .methodfinder import find`, with
  `__all__ = ["find"]`). This is the only intended public name.
- **`_find(objects, expected_value)`** (`methodfinder.py:116`) is the un-sugared entry the
  tests call directly, bypassing the `_Foo`/`==` dance. It takes the expected value as a
  normal keyword argument and returns a sorted list of strings. (The tests reach it by
  importing the module file directly — see tests-and-packaging.md — not via the package's
  `__init__`, which exports only `find`.)

## Build / run / test

Requires Python 3.10+ (the parenthesized `with` statement in `_Foo.__eq__`); the enumerated
results also shift by Python version — see the caveat below; the container pins Python 3.14. `numpy` is needed only for the numpy examples in the
tests and docstrings; it is declared as the **`test` extra** in `pyproject.toml`, not a
runtime dependency.

Day-to-day, everything runs through the container template (see the root `CLAUDE.md`):

```sh
make image        # build the Fedora-44 image (python3/numpy/ruff/ty/uv)
make format       # (container) ruff check --fix + ruff format + ty over src/
make type-check   # (container) ty + annotate-every-binding check over src/
make test         # (container) run the test suite
make shell        # interactive container shell
```

Without the container (bare host):

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
running interpreter. But the expected outputs written into the docstrings are pinned to one
Python. The docstrings were **regenerated for the container's Python 3.14** when the
container was adopted (2026-11-02) — e.g. `find(0.0) == 1.0` now lists `math.exp2(0.0)`
(added in 3.11) — so all 16 tests pass there. A doctest failure after a future Python bump
usually means "regenerate the block", not an algorithm bug. (The README's example gallery is
a looser, older snapshot, explicitly caveated as version-pinned.) Details in
[tests-and-packaging.md](tests-and-packaging.md#python-version-drift).

## Reference-doc set

- **architecture-overview.md** (this file) — what methodfinder is, layout, entry points,
  build/run/test.
- **[find-algorithm.md](find-algorithm.md)** — the `find`/`_Foo.__eq__` DSL trick and the
  search algorithm: permutations, builtins sweep, attribute sweep, the nested/type-strict
  equality test, and how results are pretty-printed as operators vs method calls.
- **[tests-and-packaging.md](tests-and-packaging.md)** — the test suite, how it is run, the
  Python-version drift, the packaging (`pyproject.toml`/`setup.py`), the `ruff` pre-commit
  hook, and `tools/behavior_diff.py` (the behavior-preservation oracle).
