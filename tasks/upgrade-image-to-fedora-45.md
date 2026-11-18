# Upgrade the image base from Fedora 44 to Fedora 45

**Status:** proposed — needs go-ahead
**Priority:** 5
**Difficulty:** 2
**Started:** 2026-11-18 (William Emerison Six <billsix@gmail.com>)

## BLUF

`Dockerfile` is `FROM registry.fedoraproject.org/fedora:44`; the container template (and every
other project in the fleet) is on Fedora 45. Move it to 45 and fix whatever the Python bump
(3.14 → 3.15) changes. Done = `make image` and the test gate pass on 45, and the docs say 45.

## Context

- References to update: `Dockerfile` (line 1, the `FROM`), `CLAUDE.md` ("Fedora-44 + Podman
  container template", the `make image` gloss "Fedora 44 + …", and "the **container's Python
  (3.14)**"), `README.md` ("Fedora 44 + Podman").
- **Expect doctest churn:** `CLAUDE.md` ("Expected-output listings drift with the Python
  version") says the doctests that hold long match lists are pinned to the container's
  Python. Python 3.15 may add builtins/`math` functions, so a failure there probably means
  "regenerate the expected block", not a bug. Check each diff before accepting it.
- The package names in `entrypoint/01-install-base.sh` should carry over, but confirm `dnf`
  resolves all of them on 45. runClaudeInContainer found `shfmt` and `procs` dropped from
  Fedora 45. methodfinder doesn't install those, but it's the kind of break to look for.

## Plan

1. Change the `FROM` to `fedora:45`; `make image`.
2. Run the test gate (and `make type-check`); regenerate any Python-version-dependent expected
   output, reviewing each diff.
3. Update the 44/3.14 mentions in `CLAUDE.md` and `README.md`. Add a `CHANGELOG.md`
   `[Unreleased]` entry if the repo has one and the supported Python changed.
