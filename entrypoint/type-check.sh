#!/usr/bin/env bash
#
# Read-only type gate: ty over the source (no --fix, nothing mutated), plus the
# annotate-every-binding completeness checker (tools/check_local_annotations.py, which
# enforces the house rule `ty` cannot). Every step runs and the script exits nonzero if
# ANY failed (status accumulates), so one run reports all the red.
#
# Portable: container (cd /methodfinder) and host (repo root) both work; the venv
# activate is guarded and paths are relative.

export VIRTUAL_ENV_DISABLE_PROMPT=1
[ -f /venv/bin/activate ] && source /venv/bin/activate
[ -d /methodfinder ] && cd /methodfinder

status=0
ty check src || status=1
# --include-module also flags un-annotated module-level globals, not just locals.
python tools/check_local_annotations.py --include-module src || status=1
exit $status
