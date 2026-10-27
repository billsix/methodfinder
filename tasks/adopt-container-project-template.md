# Adopt the container-per-project template (Dockerfile + Makefile + entrypoint/)

**Status:** proposed — needs go-ahead.
**Priority:** 4
**Difficulty:** 4
**Created:** 2026-10-27 (William Emerison Six <billsix@gmail.com>)
**Updated:** 2026-10-27 (William Emerison Six <billsix@gmail.com>)

## BLUF

Bring methodfinder up to the maintainer's standard **container-per-project template** — the
Fedora-44 + podman ephemeral-container setup every other Python project here uses (`Dockerfile`,
`Makefile` of `podman run --rm` targets, `entrypoint/` scripts). "Done" = `make image` builds,
`make shell`/`make shell-exec` drop into the project env, `make format`/`make type-check`/`make
test` run the gates in-container, and the layout matches the template's invariant tier. This is the
**prerequisite** for wiring a real test gate, so it unblocks [[migrate-unit-tests-to-doctests]].

## Context (cold start)

- Repo: github.com/billsix/methodfinder — a single ~390-line module
  (`src/methodfinder/methodfinder.py`) + `methodfinder-test.py` (16 `unittest` cases;
  `numpy` needed by the tests only). `src/` layout, `pyproject.toml`/`setup.py`/`setup.cfg`.
- **No container template today:** no `Dockerfile`, no `Makefile`, no `entrypoint/`. Tests run by
  hand (`cd src/methodfinder && PYTHONPATH=../ python3 methodfinder-test.py`). Formatting is
  **black** via `.githooks/pre-commit` — NOT the template's ruff. See `tasks/reference/tests-and-packaging.md`.

## Plan — match the template tiers

Use a conforming Python sibling as the concrete reference: **github.com/billsix/geometricalgebra**
(or `multivariate-math`), and the template spec in the maintainer's personal conventions.

1. **`Dockerfile`** — `FROM registry.fedoraproject.org/fedora:44`, the dnf-cache idiom, package
   install extracted into host-runnable `entrypoint/0N-install-*.sh` groups, `ARG` feature flags
   default `0`. Deps: python3 + numpy (tests) + the format/type-check tools; **self-contained
   image** (deps baked into committed layers, offline-capable; own source editable-installed from
   the mount at runtime).
2. **`Makefile`** — `CONTAINER_NAME = methodfinder`, `FILES_TO_MOUNT` mounting the repo at
   `/methodfinder/:Z`; targets `all`/`image`/`shell`/`shell-exec` (sharing `SHELL_RUN_FLAGS`),
   `format`, `type-check`, `test`, `image-export`/`image-import`, `help` (with `##` docs);
   `PODMAN_RUN_FLAGS` threaded into every `run`.
3. **`entrypoint/`** — `shell.sh` (`set -e`; cd; `pip install -e .`; `exec bash "$@"`),
   `format.sh`, `0N-install-*.sh` groups.
4. Verify `make image` builds and the gates run in-container.

## Decided — switch to the template's ruff + ty

**Decision (William Emerison Six <billsix@gmail.com>, 2026-10-27): drop `black`, use the template's
`ruff` + `ty`.** `entrypoint/format.sh` runs `ruff check --fix` + `ruff format`; `make type-check`
runs `ty` (+ `tools/check_local_annotations.py`, the annotate-every-binding gate, vendored from
github.com/billsix/runClaudeInContainer `tasks/reference/check_local_annotations.py`). This is the
maintainer's own repo, so a full-file ruff restyle of the single module is in bounds. Retire the
`black` config and the `.githooks/pre-commit` black hook as part of this task, and update
`README.md` / `tasks/reference/tests-and-packaging.md`, which currently document black.
