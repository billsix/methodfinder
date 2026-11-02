#!/usr/bin/env bash
# Image ENTRYPOINT (used when the image is run without the Makefile's
# `--entrypoint /bin/bash` override): activate the venv, then an interactive bash.
export VIRTUAL_ENV_DISABLE_PROMPT=1
source /venv/bin/activate
exec bash
