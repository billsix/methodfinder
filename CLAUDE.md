# methodfinder

**github.com/billsix/methodfinder** — a tiny (single-module, ~390-line) Python library
that finds the name of a function you forgot. You give it the argument(s) and the expected
result, written with `==` (a deliberate DSL: `find` returns a wrapper whose overloaded
`__eq__` runs the search and prints matches), and it prints every builtin, method,
operator, or `itertools`/`functools`/`math` function whose call produces that result. It is
a Smalltalk-80-style "method finder" for interactive REPL use. All code is in
`src/methodfinder/methodfinder.py`; `numpy` is needed only by the tests (and is not
declared as a dependency).

```sh
pip install -e .                                    # install (editable), from repo root
python3 -c "import methodfinder; methodfinder.find([]) == 0"   # use it
cd src/methodfinder && PYTHONPATH=../ python3 methodfinder-test.py   # run the 16 tests
```

The test file's name has a hyphen (`methodfinder-test.py`), so pytest/`-m unittest` do not
discover it — run it directly as above. Formatting is **black**, enforced by
`.githooks/pre-commit` (enable with `git config core.hooksPath .githooks`). Note: the
expected-output listings in the README and doctests are pinned to one Python version and
drift as newer Pythons add builtins/`math` functions — a failing doctest after an upgrade
usually means "regenerate the expected block", not an algorithm bug.

## Reference docs (`tasks/reference/`)

- **[architecture-overview.md](tasks/reference/architecture-overview.md)** — what it is,
  layout, entry points, build/run/test. Start here.
- **[find-algorithm.md](tasks/reference/find-algorithm.md)** — the `==` DSL trick and the
  search algorithm (permutations, builtins sweep, attribute sweep, nested/type-strict
  equality, operator-vs-method pretty-printing).
- **[tests-and-packaging.md](tasks/reference/tests-and-packaging.md)** — the test suite,
  how to run it, Python-version drift, packaging metadata, and the pre-commit hook.

## Conventions

Follow Bill's global conventions (task docs under `tasks/`, reference docs under
`tasks/reference/` never archived, stage by path and don't commit, refer to the project by
its GitHub URL in committed text). This repo has no container/Makefile setup — it is a plain
`pip install -e .` package tested by running one file.
