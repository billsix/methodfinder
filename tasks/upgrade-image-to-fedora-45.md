# Upgrade the image base from Fedora 44 to Fedora 45 (done)

**Done:** 2026-11-18 (William Emerison Six <billsix@gmail.com>)

`Dockerfile` moved from `FROM registry.fedoraproject.org/fedora:44` to `fedora:45`, which
brings Python 3.14 → 3.15.2. Every package in `entrypoint/01-install-base.sh` still resolved.
`CLAUDE.md` and `README.md` now say Fedora 45, and CLAUDE.md's doctest note says the doctests
are pinned to Python 3.15.

Verified nested on 2026-11-18: `make image`; `make test` (16 tests OK); `make type-check` (clean);
and the module doctests, which no make target runs, run the way `entrypoint/test.sh` runs the
tests (`cd src/methodfinder && PYTHONPATH=.. python3 -m doctest methodfinder.py`): 20 passed.
None of the expected-output listings changed on 3.15. Run from another directory, the doctests
fail with `AttributeError: module 'methodfinder' has no attribute …`, because they name the
module `methodfinder` as `test.sh`'s cwd makes it. That is how the doctests are written, not a
3.15 change.
