# Tests, running, and packaging

## The test suite

All tests live in one file, `src/methodfinder/methodfinder-test.py`, a `unittest` module
with 16 test methods on `TestMethodFinder`:

- **15 example-based cases** (`methodfinder-test.py:29-129`, `:135-146`) call
  `methodfinder._find([...], expected_value=...)` — the un-sugared entry point, so they
  don't rely on the `==` DSL — and assert the exact sorted list of match strings. They
  cover the operator paths (`test_add`, `test_divide`, `test_one_one_one`), the `in`/join
  paths (`test_in`, `test_join`), iterator results (`test_zip`, `test_permutations`), and
  the numpy path (`test_numpy`, `:135`).
- **1 doctest case** (`test_doctest`, `:131-133`) runs `doctest.testmod(methodfinder)` and
  asserts zero failures, exercising the docstrings in `methodfinder.py` (the module
  docstring examples in `find` and `_Foo`, plus `_test_for_equality_...` and
  `_repr_arg_list`).

`numpy` is imported at module top (`:25`) and inside `test_numpy` (`:136`), so the whole
file needs numpy present to run at all.

## How to run it

The filename is `methodfinder-test.py` **with a hyphen**. That matters:

- A hyphen is illegal in a Python module name, so `python -m unittest methodfinder-test`
  and `import`-based discovery cannot load it.
- pytest's default discovery globs `test_*.py` and `*_test.py`; `methodfinder-test.py`
  (hyphen, and `-test` not `_test`) matches **neither**, so a bare `pytest` will not
  collect it either.

The working invocation is to run the file directly (it has
`if __name__ == "__main__": unittest.main()` at `:149-150`), with `methodfinder`
importable:

```sh
cd src/methodfinder && PYTHONPATH=../ python3 methodfinder-test.py
# or, after `pip install -e .` from the repo root:
python3 src/methodfinder/methodfinder-test.py
```

Verified in-sandbox on **Python 3.14.6 with numpy 2.4.6**: `Ran 16 tests`, 15 pass, 1
fails (`test_doctest`) — see the next section. (Run inside the plain sandbox, not a
project container; there is no Dockerfile/Makefile in this repo.)

## Python-version drift

The algorithm enumerates whatever the running interpreter exposes, so the *set of matches*
grows as Python adds builtins/`math` functions. The expected outputs baked into the README
and docstrings are snapshots of one interpreter version and drift out of date:

- On Python 3.14, the docstring example `find(0.0) == 1.0` (`methodfinder.py:46-50`)
  expects `math.cos/cosh/erfc/exp` but the interpreter now also matches `math.exp2` (added
  in 3.11), so `test_doctest` fails on the extra line. The 15 non-doctest tests still pass.
- The commit history shows this is a recurring maintenance chore, not a defect:
  `c47f47e "apparently python 3.9 added some methods"` updated the expected lists for 3.9.
  The unit tests themselves have already been updated past that — e.g. `test_doublenegative`
  (`:88-98`) expects `-1.bit_count()`, which only exists on Python 3.10+.
- The README (`README.md`) is an even older snapshot: e.g. it lists `find([1,2,3]) == 6`
  as only `sum([1,2,3])` (`README.md:40-41`), while the current code/docstring also yields
  `math.prod([1,2,3])`.

**Takeaway for a maintainer:** when a doctest fails after a Python upgrade, the fix is
usually to regenerate the expected-output block for the new interpreter, not to change the
algorithm. Keeping README/docstrings/tests in sync across Python versions is the main
upkeep this project needs.

## Packaging

Three overlapping metadata files, src-layout:

- **`pyproject.toml`** — PEP 517 build (`setuptools`) and PEP 621 metadata: name
  `methodfinder`, **version `0.0.5`**, MIT license, author William Emerison Six.
- **`setup.cfg`** — `[options]` with `package_dir = =src` / `packages = find:` (the
  src-layout wiring) and an `install_requires` of `mypy`, `mypy-extensions`, `typed-ast`,
  `typing-extensions`. **Note:** those are type-checking/dev tools, not runtime
  dependencies — importing `methodfinder` needs none of them. `numpy`, which the *tests*
  need, is **not** listed anywhere.
- **`setup.py`** — a 4-line shim calling `setup()` so `pip install -e .` / `sdist` work.

**Version-tag mismatch:** `pyproject.toml` declares `0.0.5`, but the newest git tag is
`0.0.3` (`git tag --sort=v:refname` → `0.0.1 0.0.2 0.0.3`). So the two most recent version
bumps are untagged.

Install for development from the repo root:

```sh
pip install -e .
```

## The pre-commit hook

`.githooks/pre-commit` (not installed by default — `git config core.hooksPath .githooks`
to enable) does two things on commit: (1) rejects non-ASCII filenames, and (2) runs
`black` on every staged `*.py` file and re-stages it (`.githooks/pre-commit:48-52`), then
runs `git diff-index --check` for whitespace errors. So the repo's formatting convention is
**black defaults**, enforced at commit time. There is no linter, type-check gate, or CI
workflow in the repo despite `mypy` being listed in `install_requires` — the history shows
mypy was run manually (`13f1ec0 "pass mypy type checker"`).
