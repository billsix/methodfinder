.DEFAULT_GOAL := help

CONTAINER_CMD ?= $(shell command -v podman >/dev/null 2>&1 && echo podman || echo docker)
CONTAINER_NAME = methodfinder

# Extra flags for every container `run`. Auto-set when running nested inside a
# runClaudeInContainer/runCrushInContainer sandbox (which exports NESTED_PODMAN=1, making
# --cgroups=disabled apply so podman-in-podman works); empty -- and byte-identical
# behavior -- on a normal host. Overridable: make test PODMAN_RUN_FLAGS='--cgroups=disabled'.
# On `run` lines only, never `build` (podman build rejects --cgroups). Convention:
# runClaudeInContainer tasks/reference/nested-podman-design.md.
PODMAN_RUN_FLAGS ?= $(if $(filter 1,$(NESTED_PODMAN)),--cgroups=disabled)

TMUX_FILE := $(HOME)/.tmux.conf
TMUX_REAL_PATH := $(shell readlink -f $(TMUX_FILE))
TMUX_MOUNT := $(shell if [ -f $(TMUX_REAL_PATH) ]; then echo "-v $(TMUX_REAL_PATH):/root/.tmux.conf:Z" ; fi)

GITCONFIG_FILE := $(HOME)/.gitconfig
GITCONFIG_REAL_PATH := $(shell readlink -f $(GITCONFIG_FILE))
GITCONFIG_MOUNT := $(shell if [ -f $(GITCONFIG_REAL_PATH) ]; then echo "-v $(GITCONFIG_REAL_PATH):/root/.gitconfig:Z" ; fi)

GNUPG_FILE := $(HOME)/.gnupg
GNUPG_REAL_PATH := $(shell readlink -f $(GNUPG_FILE))
GNUPG_MOUNT := $(shell if [ -d $(GNUPG_REAL_PATH) ]; then echo "-v $(GNUPG_REAL_PATH):/root/.gnupg:Z" ; fi)

# The whole repo is mounted at /methodfinder; the entrypoint scripts are mounted
# individually so edits to them take effect without an image rebuild.
FILES_TO_MOUNT = -v $(shell pwd):/methodfinder/:Z \
		-v ./entrypoint/entrypoint.sh:/entrypoint.sh:Z \
		-v ./entrypoint/format.sh:/format.sh:Z \
		-v ./entrypoint/type-check.sh:/type-check.sh:Z \
		-v ./entrypoint/test.sh:/test.sh:Z \
		$(TMUX_MOUNT) \
		$(GNUPG_MOUNT) \
		$(GITCONFIG_MOUNT)

.PHONY: all
all: image shell ## Build the image and go into the shell

.PHONY: image
image: ## Build the OCI image
	$(CONTAINER_CMD) build -t $(CONTAINER_NAME) .

# --- shell / shell-exec share ONE container invocation, defined here so the two targets
# can never drift. Scoped to this pair ONLY. See runClaudeInContainer
# tasks/add-shell-exec-target.md for the design.
SHELL_RUN_FLAGS = \
		--entrypoint /bin/bash \
		$(FILES_TO_MOUNT) \
		-v ./entrypoint/shell.sh:/shell.sh:Z

# In-container repo mount path (matches FILES_TO_MOUNT: -v $(pwd):/methodfinder/).
REPO_MOUNT = /methodfinder

# shell-exec payload: cd to the repo root (independent of shell.sh's own cd), then run the
# inline CMD, else the repo-relative SCRIPT. Prefers CMD when both are set.
SHELL_EXEC_ARGS = -c 'cd $(REPO_MOUNT) && $(if $(CMD),$(CMD),exec bash $(SCRIPT))'

.PHONY: shell
shell: ## Get a shell into an ephemeral container made from the image
	$(CONTAINER_CMD) run $(PODMAN_RUN_FLAGS) -it --rm $(SHELL_RUN_FLAGS) $(CONTAINER_NAME) /shell.sh

.PHONY: shell-exec
shell-exec: image ## Run a script/command in the container env (no TTY): make shell-exec SCRIPT=path | CMD='...'
	@[ -n "$(SCRIPT)$(CMD)" ] || { echo 'usage: make shell-exec SCRIPT=<repo-relative path> | CMD="..."'; exit 2; }
	$(CONTAINER_CMD) run $(PODMAN_RUN_FLAGS) --rm $(SHELL_RUN_FLAGS) $(CONTAINER_NAME) /shell.sh $(SHELL_EXEC_ARGS)

# Run ruff + ty over the source INSIDE the container (the image's pinned toolchain). The
# editable install overlays the image's baked copy with the live bind-mounted tree first,
# so ruff/ty see what's on disk.
.PHONY: format
format: image ## (container) ruff check --fix + ruff format + ty over src (entrypoint/format.sh)
	$(CONTAINER_CMD) run $(PODMAN_RUN_FLAGS) --rm \
		--entrypoint /bin/bash \
		$(FILES_TO_MOUNT) \
		$(CONTAINER_NAME) \
		-c 'set -e; source /venv/bin/activate; cd /methodfinder; \
		    uv pip install --python $$(which python) --no-deps --no-index --no-build-isolation -e .; \
		    bash /format.sh'

# Read-only type gate: ty (no --fix) + the annotate-every-binding checker.
.PHONY: type-check
type-check: image ## (container) ty + local-annotation check over src (entrypoint/type-check.sh)
	$(CONTAINER_CMD) run $(PODMAN_RUN_FLAGS) --rm \
		--entrypoint /bin/bash \
		$(FILES_TO_MOUNT) \
		$(CONTAINER_NAME) \
		-c 'set -e; source /venv/bin/activate; cd /methodfinder; \
		    uv pip install --python $$(which python) --no-deps --no-index --no-build-isolation -e .; \
		    bash /type-check.sh'

# Run the test suite INSIDE the container. The hyphenated test file is run directly (NOT
# pytest -- it isn't discoverable); numpy is baked into the image's venv. Exit 0 on
# success, nonzero on failure.
.PHONY: test
test: image ## (container) run the test suite (methodfinder-test.py, run directly)
	$(CONTAINER_CMD) run $(PODMAN_RUN_FLAGS) --rm \
		--entrypoint /bin/bash \
		$(FILES_TO_MOUNT) \
		$(CONTAINER_NAME) \
		/test.sh

.PHONY: image-export
image-export: ## export the OCI image to a timestamped tar in the repo root
	$(CONTAINER_CMD) save $(CONTAINER_NAME) -o $(CONTAINER_NAME)-$(shell date +%m-%d-%Y_%H-%M-%S).tar

.PHONY: image-import
image-import: ## import an OCI image tar: make image-import FILE=foo.tar
	$(CONTAINER_CMD) load -i $(FILE)

.PHONY: help
help:
	@grep --extended-regexp '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
