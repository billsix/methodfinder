# Add a `.dockerignore`

Done 2026-11-08 (William Emerison Six <billsix@gmail.com> asked for it), on branch `add-dockerignore`.

## What changed

`COPY src /methodfinder/src` had no `.dockerignore` in front of it, so the host's
`src/methodfinder/__pycache__/` was baked into the image. The new `.dockerignore` excludes `.git`,
`**/__pycache__/`, `**/*.py[cod]`, `**/.pytest_cache/`, `**/.ruff_cache/`, `**/*.egg-info/`, `.crush/`
and `*.tar`.

The first version used `__pycache__/` (as github.com/billsix/geometricalgebra's does). That did not
work: `.dockerignore` patterns are anchored at the context root, unlike `.gitignore`, so a nested
`__pycache__` needs `**/`. The rebuilt image showed the host `.pyc` files (host timestamps) until the
patterns were anchored. This trap is now in the Dockerfile contract's `.dockerignore` bullet (personal
overlay, github.com/billsix/dotfiles `.ai-coding-conventions.personal.md`).

## Verification (2026-11-08, nested podman)

- `make image` succeeded.
- `find /methodfinder -name __pycache__` in the image: 0 (was 1 before the `**/` fix).
- `python -c "import methodfinder"` in the image's venv: ok.
