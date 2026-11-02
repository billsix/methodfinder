#!/usr/bin/env bash
#
# Run methodfinder's test suite. The test file is `methodfinder-test.py` -- the HYPHEN
# makes it an illegal module name, so neither `pytest` nor `python -m unittest` discovers
# it; it must be run directly as a script. numpy (a test-only dep, baked into the image's
# venv) must be importable.
#
# (The separate migrate-unit-tests-to-doctests task will later move the version-stable
# cases to `--doctest-modules`; until then this is the faithful direct invocation.)
#
# Portable: container (cd /methodfinder) and host (repo root) both work.
set -e
export VIRTUAL_ENV_DISABLE_PROMPT=1
[ -f /venv/bin/activate ] && source /venv/bin/activate
[ -d /methodfinder ] && cd /methodfinder

# PYTHONPATH=.. puts src/ on the path so `import methodfinder` resolves even without the
# editable install; run from src/methodfinder so the script's own name is importable.
cd src/methodfinder
PYTHONPATH=.. python3 methodfinder-test.py
