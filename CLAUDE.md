# methodfinder

**github.com/billsix/methodfinder** — a tiny (single-module, ~390-line) Python library
that finds the name of a function you forgot. You give it the argument(s) and the expected
result, written with `==` (a deliberate DSL: `find` returns a wrapper whose overloaded
`__eq__` runs the search and prints matches), and it prints every builtin, method,
operator, or `itertools`/`functools`/`math` function whose call produces that result. It is
a Smalltalk-80-style "method finder" for interactive REPL use. All library code is in
`src/methodfinder/methodfinder.py`; it has **no third-party runtime dependencies**. `numpy`
is a **test-only** dependency, declared as the `test` extra in `pyproject.toml` (not a
runtime dep).

## Dev environment — the container-per-project template

This repo uses the standard Fedora-44 + Podman container template (`Dockerfile`, `Makefile`
of `podman run --rm` targets, `entrypoint/` scripts). It's the minimal **pure-Python** case:
base-only, no GUI/docs/jupyter/emacs groups. Run everything through `make` (labels:
`[HOST]` runs on your machine, which builds/launches the container):

```sh
make image        # [HOST] build the OCI image (Fedora 44 + python3/numpy/ruff/ty/uv)
make shell        # [HOST] interactive container shell (editable self-install done on entry)
make format       # [HOST] (container) ruff check --fix + ruff format + ty over src/
make type-check   # [HOST] (container) ty + annotate-every-binding checker over src/
make test         # [HOST] (container) run the test suite
make help         # [HOST] list all targets
```

- **`numpy` is a test-only extra**, installed from dnf into the image's `--system-site-packages`
  venv; the library imports only the standard library.
- **Self-contained image + live source:** all deps are baked at image-build time (offline
  forever); only methodfinder's own source is editable-installed from the bind mount at
  runtime, so host edits propagate without a rebuild. The source is also baked (`COPY`) so an
  exported/loaded image runs offline with no mount.

## Gate: ruff + ty (black has been retired)

Formatting/linting is **ruff** (line length 88, `select = E/F/I`), type-checking is **ty**,
plus `tools/check_local_annotations.py` (the "annotate every binding" completeness check ty
can't do). The old `black` pre-commit hook now runs ruff instead. `tools/check_local_annotations.py`
is a **SHARED, VENDORED** tool — canonical copy in github.com/billsix/runClaudeInContainer
`tasks/reference/check_local_annotations.py`; edit the canonical and re-copy, keep byte-identical.

## Gotchas

- **The test file is `methodfinder-test.py` (hyphen).** An illegal module name, so neither
  `pytest` nor `python -m unittest` discovers it — it is **run directly** (`entrypoint/test.sh`
  does `cd src/methodfinder && PYTHONPATH=.. python3 methodfinder-test.py`). The ruff/ty gate
  **excludes** this file (`*-test.py`): its name/star-import issues are owned by the
  migrate-unit-tests-to-doctests task (`tasks/migrate-unit-tests-to-doctests.md`), which will
  rework it; don't lint/type it until then.
- **Expected-output listings drift with the Python version.** The code enumerates whatever
  the running interpreter exposes, so a doctest holding a long match list (e.g.
  `find(0.0) == 1.0`) grows as newer Pythons add builtins/`math` functions. The doctests are
  pinned to the **container's Python (3.14)**; a failure after a Python bump usually means
  "regenerate the expected block", not an algorithm bug.

## Reference docs (`tasks/reference/`)

- **[architecture-overview.md](tasks/reference/architecture-overview.md)** — what it is,
  layout, entry points, build/run/test. Start here.
- **[find-algorithm.md](tasks/reference/find-algorithm.md)** — the `==` DSL trick and the
  search algorithm (permutations, builtins sweep, attribute sweep, nested/type-strict
  equality, operator-vs-method pretty-printing).
- **[tests-and-packaging.md](tasks/reference/tests-and-packaging.md)** — the test suite,
  how to run it, Python-version drift, packaging metadata, the container gate, and the
  (now ruff) pre-commit hook.

## Conventions

Follow Bill's global conventions (task docs under `tasks/`, reference docs under
`tasks/reference/` never archived, stage by path and don't commit, refer to the project by
its GitHub URL in committed text).
