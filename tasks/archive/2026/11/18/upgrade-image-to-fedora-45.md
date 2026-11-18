# Upgrade the image base from Fedora 44 to Fedora 45 (done)

**Done:** 2026-11-18 (William Emerison Six <billsix@gmail.com>)

`Dockerfile` moved from `FROM registry.fedoraproject.org/fedora:44` to `fedora:45`, which
brings Python 3.14 → 3.15.2. Every package in `entrypoint/01-install-base.sh` still resolved.
`CLAUDE.md` and `README.md` now say Fedora 45, and CLAUDE.md's doctest note says the doctests
are pinned to Python 3.15.

Verified nested on 2026-11-18: `make image`; `make test` (16 tests OK); `make type-check` (clean);
and the module doctests: `make test`'s `test_doctest` case runs
`doctest.testmod(methodfinder)`, and a separate run of
`cd src/methodfinder && PYTHONPATH=.. python3 -m doctest -v methodfinder.py` showed all 20
passing. None of the expected-output listings changed on 3.15.
