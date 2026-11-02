FROM registry.fedoraproject.org/fedora:44

# methodfinder is a single-module pure-Python library with NO optional feature groups
# (no GUI, docs, jupyter, or emacs), so there are no ARG feature flags and just one
# package-install script (entrypoint/01-install-base.sh).

COPY entrypoint/dotfiles/ /root/
COPY entrypoint/entrypoint.sh /entrypoint.sh

# System-package installation lives in a host-runnable script (entrypoint/01-install-base.sh)
# so the exact same package set can be installed on a bare Fedora host/guest, not only
# during this build. The dnf CACHE MOUNT + `keepcache=True` stay HERE (build-time plumbing
# the script must not depend on); `dnf upgrade` also runs here, in its own earlier layer
# before the dotfiles COPY would matter. See entrypoint/01-install-base.sh for what each
# package is for.
COPY entrypoint/01-install-base.sh /usr/local/bin/
RUN --mount=type=cache,target=/var/cache/libdnf5 \
    --mount=type=cache,target=/var/lib/dnf \
    echo "keepcache=True" >> /etc/dnf/dnf.conf && \
    dnf upgrade -y && \
    /usr/local/bin/01-install-base.sh && \
    echo "source ~/.extrabashrc" >> ~/.bashrc

# A --system-site-packages venv so the dnf-installed numpy is visible to it without a
# PyPI download. setuptools/wheel are the BUILD backend for the editable install that
# shell.sh runs offline (`uv pip install --no-index --no-build-isolation -e .`, which by
# design installs no build-system.requires) -- Python 3.12+ venvs no longer seed
# setuptools, so bake it in or that install fails with ModuleNotFoundError.
RUN python3 -m venv --system-site-packages /venv/ && \
    export VIRTUAL_ENV_DISABLE_PROMPT=1 && source /venv/bin/activate && \
    uv pip install setuptools wheel --python /venv/bin/python

# Bake methodfinder's own source and editable-install it offline at BUILD time, into the
# same path (/methodfinder) the `make shell` bind mount uses. This keeps an exported image
# self-contained -- it imports and tests with no network and no mount -- while `make shell`
# still shadows this baked copy with the live host tree, so host edits propagate. The
# library has no third-party runtime deps, so --no-deps needs nothing from PyPI.
COPY pyproject.toml setup.py LICENSE.txt README.md /methodfinder/
COPY src /methodfinder/src
RUN export VIRTUAL_ENV_DISABLE_PROMPT=1 && source /venv/bin/activate && \
    cd /methodfinder && \
    uv pip install --python /venv/bin/python --no-deps --no-index --no-build-isolation -e .

ENTRYPOINT ["/entrypoint.sh"]
