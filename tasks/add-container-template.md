# Add a Fedora-44 + Podman dev container (Dockerfile + Makefile + entrypoint/) per my project template

**Status:** proposed — needs go-ahead. Created 2026-08-16 (William Emerison Six <billsix@gmail.com>).
**Priority:** 5
**Difficulty:** 2

## Goal

Bring methodfinder (`github.com/billsix/methodfinder`) onto my standard **container-per-project
template** — the Fedora-44 + Podman ephemeral-container dev environment (`Dockerfile`, a `Makefile` of
`podman run --rm` targets, `entrypoint/` scripts) — following the **Python family** of the template, as
multivariate-math (`github.com/billsix/multivariate-math`) and geometricalgebra
(`github.com/billsix/geometricalgebra`) do. Right now methodfinder has `pyproject.toml`/`setup.py`/`src`
but **no container**.

## What methodfinder is (constraints that shape the container)

- A tiny **single-module (~390-line) pure-Python library** (`src/methodfinder/methodfinder.py`); a
  Smalltalk-style "method finder" for the REPL.
- **`numpy` is a *test-only* dependency and is NOT declared** in `pyproject.toml` — the container must
  install it for the test target even though it isn't a runtime dep.
- **Tests are `src/methodfinder/methodfinder-test.py`** — the hyphen means pytest / `-m unittest` do
  **not** discover it; it's run directly: `cd src/methodfinder && PYTHONPATH=../ python3 methodfinder-test.py`.
- **Formatting is `black`** (enforced by `.githooks/pre-commit`), not ruff.

## Follow the template (Python family — mirror multivariate-math)

- **`Dockerfile`:** `FROM registry.fedoraproject.org/fedora:44`, the dnf-cache idiom, `dnf upgrade`,
  toolchain via a host-runnable **`01-install-base.sh`**; then create a venv
  (`python3 -m venv --system-site-packages /venv/`) and — **at build time** — `uv pip install` the
  build backend + the package's deps + the **test dep numpy** + the formatter, so an exported image is
  self-contained offline. `ARG` flags default `0`.
- **`Makefile`:** `.DEFAULT_GOAL := shell`, `CONTAINER_NAME = methodfinder`, `FILES_TO_MOUNT` with
  `-v $(shell pwd):/methodfinder/:Z` + entrypoint mounts + conditional host-config mounts; targets
  `all`→`image`→`shell`, `format`, `test`, `image-export`/`image-import`, and `help` with
  `##`-documented targets.
- **`entrypoint/`:** `shell.sh` (activate `/venv`, `cd`, offline editable self-install
  `uv pip install --no-deps --no-index --no-build-isolation -e .`, `exec bash`); `format.sh`;
  `01-install-base.sh`. A **`test.sh`** that runs the hyphenated test the direct way
  (`cd src/methodfinder && PYTHONPATH=../ python3 methodfinder-test.py`) — **not** pytest.

## Convention adherence (self-contained images + live source)

Per the container template convention: **all third-party deps (build backend, numpy, formatter)
installed at image-build time** so an exported image runs offline years later; **only methodfinder's own
package is installed at runtime** as an offline editable self-install (`-e . --no-index --no-deps`) so my
host edits propagate. No runtime network fetch.

## Open questions

1. **Keep `black` or adopt `ruff` to match the template's `format.sh`?** The template's Python
   `format.sh` is `ruff check --fix` + `ruff format`; methodfinder uses `black` (via a git pre-commit
   hook). Recommend: **keep `black`** for now (it's what the pre-commit hook enforces — switching is a
   separate decision), and have `format.sh` run `black` so the container matches the repo's actual
   formatter. Flag if you'd rather standardize on ruff. Bill's call.
2. **Declare `numpy` as a test extra?** It's currently undeclared (installed ad hoc for tests). Optional
   cleanup: add a `[project.optional-dependencies] test = ["numpy"]` and install `.[test]` at build, so
   the test dep is recorded rather than magic. Recommend yes; minor, can be deferred.
