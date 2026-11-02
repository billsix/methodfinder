#!/usr/bin/env bash
#
# Format + type-check gate: ruff check --fix, ruff format, then ty. Replaces the old
# black pre-commit hook. The line length lives in ONE place -- pyproject.toml
# [tool.ruff] line-length -- so `ruff format` here and the editor agree; no --line-length
# flag.
#
# Portable: runs in the container (cd /methodfinder) AND on the host from the repo root.
# The venv activate is guarded (absent on the host), and the ruff/ty paths are RELATIVE
# so the caller's `cd` (the container, or the .extrabashrc exit hook) decides the root.

export VIRTUAL_ENV_DISABLE_PROMPT=1
# Activate the container's venv when present; on the host it's absent, use the caller's env.
[ -f /venv/bin/activate ] && source /venv/bin/activate

# Guarded self-cd: no-op on the host (the exit hook / caller already cd'd to the root);
# in the container it pins the root regardless of the caller's cwd.
[ -d /methodfinder ] && cd /methodfinder

# Every step runs (one pass reports ALL the red), but the script exits nonzero if ANY
# step failed -- otherwise the exit code is the LAST command's alone and an earlier
# `ruff check` failure is silently masked by a clean `ty check`.
status=0
ruff check src --fix || status=1
ruff format src || status=1
ty check src || status=1
exit $status
