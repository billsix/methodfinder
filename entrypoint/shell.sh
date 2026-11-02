# Fail-fast setup: a failed step (venv activate, editable install) aborts rather than
# dropping you into / running a shell-exec script against a half-set-up tree. The final
# `exec bash` is a FRESH bash not under -e, so interactive/script behaviour is unchanged.
# `set -e` only (no -u).
set -e
export VIRTUAL_ENV_DISABLE_PROMPT=1
source /venv/bin/activate
cd /methodfinder/
# All dependencies are baked into the image's venv at build time (see Dockerfile); this
# only registers the live bind-mounted tree as the editable package, so container start
# needs no downloads.
uv pip install --python "$(which python)" --no-deps --no-index --no-build-isolation -e .
# No args -> interactive shell. Args (a `-c '...'` payload from `make shell-exec`) -> run
# them after setup, in a fresh bash not under -e.
exec bash "$@"
