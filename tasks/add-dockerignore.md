# Add a `.dockerignore`

**Status:** proposed — needs go-ahead. Created 2026-11-08 (William Emerison Six <billsix@gmail.com>).
**Priority:** 6
**Difficulty:** 1

## BLUF

The `Dockerfile` runs `COPY src /methodfinder/src` with no `.dockerignore`, so the host's
`src/methodfinder/__pycache__/` (present 2026-11-08) gets baked into the image, and any `.pyc` change
invalidates that layer. This is a small fix, and methodfinder is the minimal pure-Python template
example, so it should carry the file. Done = `.dockerignore` exists, `make image` succeeds, and there is
no `__pycache__` under `/methodfinder/src` in the image.

## Context

- Dockerfile contract, `.dockerignore` bullet: the personal overlay (github.com/billsix/dotfiles
  `.ai-coding-conventions.personal.md`).
- `COPY`s: `entrypoint/dotfiles/` (only `.extrabashrc`), `entrypoint/entrypoint.sh`,
  `entrypoint/01-install-base.sh`, `pyproject.toml setup.py LICENSE.txt README.md`, `src`.

## Plan

1. Add `.dockerignore`: `.git`, `__pycache__/`, `*.py[cod]`, `.ruff_cache/`, `.pytest_cache/`,
   `*.egg-info/`, `.crush/`, `*.tar`.
2. `make image`. Check: `podman run --rm --entrypoint /bin/bash methodfinder -c 'find /methodfinder -name __pycache__'`
   prints nothing.
