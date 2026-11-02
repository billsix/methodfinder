# Add a CHANGELOG and reconcile the version / git-tag mismatch

**Status:** parked — no action now. methodfinder is not published and there's no plan to publish
yet, so the versioning/changelog convention requires neither tag reconciliation nor a `CHANGELOG.md`.
Revisit only if/when it is published. (William Emerison Six <billsix@gmail.com>, 2026-11-02.)
**Priority:** 9
**Difficulty:** 2
**Created:** 2026-11-02 (William Emerison Six <billsix@gmail.com>)
**Updated:** 2026-11-02 (William Emerison Six <billsix@gmail.com>)

## BLUF

github.com/billsix/methodfinder declares `version = "0.0.5"` in `pyproject.toml` but its newest
git tag is `0.0.3`, and it has **no `CHANGELOG.md`**. If the library is pinned/consumed by anyone,
both are gaps the cross-project changelog/versioning convention wants closed. "Done" = the
version↔tag story is consistent (either the untagged bumps are tagged, or the version is corrected)
**and** — only if the library is actually consumed — a `CHANGELOG.md` exists. This is pure
packaging housekeeping; it touches no library code.

## Context (cold start)

- **The mismatch, verified 2026-11-02:** `pyproject.toml` → `version = "0.0.5"`;
  `git tag --sort=v:refname` → `0.0.1 0.0.2 0.0.3`. So the two most recent version bumps
  (`0.0.4`, `0.0.5`) were never tagged. Already documented as an open item in
  `tasks/reference/tests-and-packaging.md` ("Version-tag mismatch (still open)").
- **No evidence of a release pipeline:** no `.github/workflows/`, and `pyproject.toml` / `setup.py`
  carry no `[project.urls]`, PyPI classifiers, or twine/upload config. Whether methodfinder is
  actually published to a registry (PyPI) or pinned by any downstream is **unconfirmed** — and it
  decides whether this task needs a changelog at all (see Open questions).
- **Convention:** `~/.claude/reference/versioning-and-changelogs.md` — a project *others pin/consume*
  needs a version **and** a `CHANGELOG.md`; a private app nobody pins needs neither. Versions sort
  **as versions, not strings** (`git tag --sort=v:refname`, not plain sort). The split: the agent
  stages a bump + changelog entry; the maintainer tags and publishes.

## Plan (pending the decisions below — DO NOT execute yet)

1. **Confirm consumption** (Q1). If nobody pins it → the version/changelog machinery is optional;
   the task may reduce to removing the version pretense or leaving it as-is. If it is consumed →
   continue.
2. **Reconcile version ↔ tags** (Q2): either retro-tag `0.0.4`/`0.0.5` at the commits where those
   bumps happened (find them via `git log -p -- pyproject.toml setup.cfg`), or treat current HEAD as
   the next release and tag forward. Tagging is the maintainer's step; the agent only identifies the
   right commits and proposes the tags.
3. **Add `CHANGELOG.md`** (Q3): Keep-a-Changelog format, newest-first, `[Unreleased]` at top, then
   `## [version] — date`, breaking items called out. Retro-fill from git history to whatever depth
   is chosen.
4. Update `tasks/reference/tests-and-packaging.md` (drop the "still open" note once reconciled) and
   `CLAUDE.md`/`README.md` if a release/changelog step is now part of the workflow.

## Decided (William Emerison Six <billsix@gmail.com>, 2026-11-02) — no action now

1. **Published/consumed?** No — methodfinder is not published anywhere and there's no plan to
   publish yet. By the versioning/changelog convention a project nobody pins needs **neither
   version discipline nor a `CHANGELOG.md`**, so no changelog is added.
2. **Tags?** Leave them. The untagged `0.0.4`/`0.0.5` are not reconciled and no new tags are made.
3. **CHANGELOG retro-fill?** Not applicable — no changelog.

The `version = "0.0.5"` string in `pyproject.toml` stays as an internal marker; the tag gap is
intentional, not a defect, while the project is unpublished. **Revisit this task only if/when
methodfinder is published** — then tag reconciliation and a `CHANGELOG.md` become warranted, and
the plan above applies.
