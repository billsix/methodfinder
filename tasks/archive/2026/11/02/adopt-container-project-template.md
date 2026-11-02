# Adopt the container-per-project template (Dockerfile + Makefile + entrypoint/)

**Status:** done — work committed; archived 2026-11-02.
**Priority:** 4
**Difficulty:** 4
**Created:** 2026-10-27 (William Emerison Six <billsix@gmail.com>)
**Updated:** 2026-11-02 (William Emerison Six <billsix@gmail.com>)

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

**Decision (William Emerison Six <billsix@gmail.com>, 2026-11-02, two questions asked at
implementation time):**
1. **How green?** → **Full green.** The single module was brought fully to standard: ruff-reformatted,
   every binding annotated (ty + `check_local_annotations` clean), and the safe code nits fixed
   (`not x in`→`x not in`, `type ==`→`is`, ambiguous `l`→`args`, redundant `cast` dropped, dup
   `import itertools` + "writcten" typo removed). **One obvious fix was deliberately NOT applied:**
   the three bare `except:` clauses stay (with `# noqa: E722` + reason) — changing them to
   `except Exception:` broke the algorithm, because the builtins sweep probes `exit()`/`quit()`
   which raise `SystemExit` (a `BaseException`), and the bare except must swallow it.
2. **Doctest version drift?** → **Regenerate to green.** The `find(0.0) == 1.0` docstring block was
   regenerated for the container's Python 3.14 (added `math.exp2(0.0)`), so all 16 tests pass. The
   docstrings are now pinned to 3.14.

## Done — what was built + verified (2026-11-02)

Added: `Dockerfile` (Fedora-44, base-only — no GUI/docs/jupyter/emacs; bakes deps + own source for
offline self-containment), `Makefile` (`all`/`image`/`shell`/`shell-exec`/`format`/`type-check`/
`test`/`image-export`/`image-import`/`help`, `PODMAN_RUN_FLAGS`, shared `SHELL_RUN_FLAGS`,
`REPO_MOUNT=/methodfinder`), `entrypoint/{01-install-base.sh,shell.sh,format.sh,type-check.sh,
test.sh,entrypoint.sh,dotfiles/.extrabashrc}`, `tools/check_local_annotations.py` (byte-identical
vendored copy). Changed: `pyproject.toml` (src-layout folded in from the deleted `setup.cfg`,
`dependencies=[]`, `test`/`dev` extras, ruff/ty config; fixed the garbled description),
`.githooks/pre-commit` (black→ruff), `src/methodfinder/__init__.py` (explicit `find` import +
`__all__`), `src/methodfinder/methodfinder.py` (the full-green cleanup above). Removed: `setup.cfg`.
Docs updated: `CLAUDE.md`, `README.md`, `tasks/reference/{architecture-overview,find-algorithm,
tests-and-packaging}.md`.

**Verified in-container, nested podman (Python 3.14.8, numpy 2.4.6):** `make image` builds (offline
editable self-install OK); `make format` exit 0 (ruff + ty clean); `make type-check` exit 0 (ty +
annotations clean); `make test` exit 0 (16/16 OK). `make help` and `make shell-exec CMD=…` work.

**Scope note:** the gates exclude the hyphenated `methodfinder-test.py` (ruff `extend-exclude` +
`[tool.ty.src] exclude`); its invalid-module-name/star-import issues belong to
[[migrate-unit-tests-to-doctests]], which is now unblocked (it has a real `make test` to wire into).

**Archive:** done 2026-11-02 — the container-adoption work landed in the maintainer's work commit on
`master`, and this doc was then `git mv`'d to `tasks/archive/2026/11/02/` as its own archive commit.
