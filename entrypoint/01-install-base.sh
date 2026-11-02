#!/usr/bin/env bash
#
# 01-install-base.sh -- the always-needed Fedora packages for methodfinder.
#
# One package group per script, and the script takes NO options: methodfinder has no
# optional feature groups, so this is the only install script. Same packages whether run
# during `podman build`, on a bare Fedora host, or in a guest with no container runtime.
# `dnf upgrade` stays in the Dockerfile (it runs in its own earlier layer, before the
# dotfiles COPY), so this script is purely `dnf install`.
#
# What each package is for:
#   python3{,-pip,-setuptools,-wheel} -- interpreter + the editable-install build backend
#                                        (Python 3.12+ venvs no longer seed setuptools, so
#                                        the venv's offline `uv pip install -e .` needs it).
#   python3-numpy -- a TEST-ONLY dependency: methodfinder-test.py and the numpy doctests
#                    need it, but the library itself has NO runtime dependencies. From dnf
#                    so the --system-site-packages venv sees it without a PyPI download.
#   ruff, ty      -- the format + type-check gate (replaces the old black hook).
#   uv            -- the offline editable self-install at container start (shell.sh).
#   git, tmux, which -- dev conveniences / tooling the entrypoint scripts rely on.
#
# Several dnf calls, so accumulate a non-zero exit if any fails (don't let a later
# success mask an earlier failure).
set -uo pipefail

if ! command -v dnf >/dev/null 2>&1; then
    echo "01-install-base.sh: needs 'dnf' (this installs Fedora packages), not found." >&2
    echo "Run on a Fedora host/guest, or inside the project's Fedora-based image." >&2
    exit 1
fi

status=0

dnf install -y \
    git \
    python3 \
    python3-numpy \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    ruff \
    tmux \
    ty \
    uv \
    which || status=1

exit $status
