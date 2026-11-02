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
`if __name__ == "__main__": unittest.main()` at the bottom), with `methodfinder`
importable. Run from `src/methodfinder` so the script's own directory is `sys.path[0]`:
then `import methodfinder` resolves to the sibling `methodfinder.py` **module** (not the
installed package), which is how the tests reach the underscore-prefixed `_find` etc.

```sh
# in the container (the normal path):
make test                 # runs entrypoint/test.sh = the direct invocation below
# by hand, on the host:
cd src/methodfinder && PYTHONPATH=../ python3 methodfinder-test.py
```

Verified in the project container (**Python 3.14.8, numpy 2.4.6**, 2026-11-02):
`make test` → `Ran 16 tests ... OK` (all 16 pass, including `test_doctest`, after the
docstrings were regenerated for 3.14 — see the next section).

## Python-version drift

The algorithm enumerates whatever the running interpreter exposes, so the *set of matches*
grows as Python adds builtins/`math` functions. The expected outputs baked into the README
and docstrings are snapshots of one interpreter version and drift out of date:

- The docstrings are now pinned to the **container's Python 3.14**: when the container was
  adopted (2026-11-02) the `find(0.0) == 1.0` block in `methodfinder.py`'s `find` docstring
  was regenerated to include `math.exp2(0.0)` (added in 3.11), so `test_doctest` passes.
  Before that it failed on the missing `math.exp2` line while the 15 non-doctest tests passed.
- The commit history shows this is a recurring maintenance chore, not a defect:
  `c47f47e "apparently python 3.9 added some methods"` updated the expected lists for 3.9.
  The unit tests themselves have already been updated past that — e.g. `test_doublenegative`
  expects `-1.bit_count()`, which only exists on Python 3.10+.
- The README is an even older, looser snapshot (e.g. it lists `find([1,2,3]) == 6` as only
  `sum([1,2,3])` while the current code/docstring also yields `math.prod([1,2,3])`); its
  intro now carries an explicit "pinned to one version, regenerate on drift" caveat, so it is
  left as an illustrative gallery rather than kept byte-exact.

**Takeaway for a maintainer:** when a doctest fails after a Python upgrade, the fix is
usually to regenerate the expected-output block for the new interpreter, not to change the
algorithm. Keeping docstrings/tests in sync across Python versions is the main upkeep this
project needs. (The forthcoming migrate-unit-tests-to-doctests task will consolidate the
version-stable cases as doctests and keep the fragile long-list ones as plain tests.)

## Packaging

Src-layout, two metadata files (`setup.cfg` was removed when the container was adopted):

- **`pyproject.toml`** — PEP 517 build (`setuptools`) and PEP 621 metadata: name
  `methodfinder`, **version `0.0.5`**, MIT license, author William Emerison Six. It also
  carries the src-layout wiring (`[tool.setuptools.packages.find] where = ["src"]`, moved
  here from the deleted `setup.cfg`), the ruff config (`line-length = 88`, `select =
  E/F/I`, `extend-exclude = ["*-test.py"]`), and the ty exclude for the test file.
  `dependencies = []` (no runtime deps); `numpy` is the **`test` extra**; `ruff`/`ty` are the
  `dev` extra.
- **`setup.py`** — a 4-line shim calling `setup()` so `pip install -e .` / `sdist` work.

**Version-tag gap (intentional while unpublished):** `pyproject.toml` declares `0.0.5`, but the
newest git tag is `0.0.3` (`git tag --sort=v:refname` → `0.0.1 0.0.2 0.0.3`), so `0.0.4`/`0.0.5`
are untagged. This is **left as-is by decision** (William Emerison Six <billsix@gmail.com>,
2026-11-02): methodfinder is not published and has no publish plan, so the versioning convention
requires neither tag reconciliation nor a `CHANGELOG.md`. Revisit if it is ever published — see the
parked `tasks/changelog-and-version-tagging.md`.

## The gate: container `make` targets + the pre-commit hook

The repo now has a containerized gate (adopted 2026-11-02, replacing hand-run tooling):

- **`make format`** — `ruff check --fix` + `ruff format` + `ty check` over `src/`
  (`entrypoint/format.sh`).
- **`make type-check`** — `ty check` + `tools/check_local_annotations.py --include-module`
  (the annotate-every-binding completeness gate) over `src/` (`entrypoint/type-check.sh`).
- **`make test`** — the direct test-file run (`entrypoint/test.sh`).

All three exclude the hyphenated test file from ruff/ty (via `extend-exclude` / `[tool.ty.src]
exclude`), since its invalid-module-name/star-import issues are the migrate-unit-tests-to-doctests
task's to resolve.

`.githooks/pre-commit` (not installed by default — `git config core.hooksPath .githooks`
to enable) does two things on commit: (1) rejects non-ASCII filenames, and (2) runs **ruff**
(`ruff check --fix` + `ruff format`, replacing the old `black` loop, 2026-11-02) on every
staged `*.py` file and re-stages it, then runs `git diff-index --check` for whitespace
errors. So the repo's formatting convention is **ruff** (line length 88), enforced both at
commit time and by `make format`. Type-checking (`ty`) superseded the old manually-run
`mypy` (`13f1ec0 "pass mypy type checker"`), whose stale `install_requires` entry was
dropped with `setup.cfg`.

## Verifying a refactor preserves behavior

`tools/behavior_diff.py` is a differential-output oracle: it runs `find` over a wide query battery
and writes the exact output to a file. Snapshot before a change and after it, then `diff` the two —
an empty diff means the change is behavior-preserving. Output is interpreter-sensitive, so run both
snapshots on the same Python (the container's 3.14). It is **not** wired into `make test`; run it on
demand when refactoring the algorithm.
