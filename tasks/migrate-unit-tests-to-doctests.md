# Migrate unit tests into doctests and wire them into `make test`

**Status:** proposed — needs go-ahead. **Depends on** [[adopt-container-project-template]] for the
`make test` target (methodfinder has no Makefile today).
**Priority:** 5
**Difficulty:** 3
**Created:** 2026-10-27 (William Emerison Six <billsix@gmail.com>)
**Updated:** 2026-10-27 (William Emerison Six <billsix@gmail.com>)

## BLUF

Push as many of the 16 `unittest` cases as reasonable **into doctests** in
`src/methodfinder/methodfinder.py`, and run doctests as part of the project's test gate. "Done" =
the example-based cases live as `>>>` examples in the module/function docstrings, doctests run
under `make test` (once [[adopt-container-project-template]] gives us one) via
`--doctest-modules` or the existing `doctest.testmod` harness, the cases that stay `unittest` are
listed with a reason each, and the gate is green.

methodfinder is a **good fit**: it already has doctests (the module docstring, `find`, `_Foo`), and
15 of the 16 tests are already `methodfinder._find([...], expected_value=...) == <exact list>`
assertions — i.e. example → output, which is exactly a doctest.

## Context (cold start)

- Repo: github.com/billsix/methodfinder — single module `methodfinder.py` (~390 lines).
- Tests: `src/methodfinder/methodfinder-test.py`, a `unittest.TestCase` with **16** methods — 15
  example-based (`assertListEqual` of the exact match list from `_find`) + 1 (`test_doctest`) that
  runs `doctest.testmod(methodfinder)` and asserts zero failures. `numpy` is needed to run the file
  at all. Full map: `tasks/reference/tests-and-packaging.md`.
- **Two gotchas that shape this:**
  - The file is `methodfinder-test.py` (hyphen, `-test` not `_test`) so neither `pytest` nor
    `-m unittest` discovers it — it is run directly. If we move to a pytest `--doctest-modules`
    gate, that doesn't matter (doctests live in `methodfinder.py`); if we keep a unittest file,
    decide whether to rename it `methodfinder_test.py`.
  - The expected-output lists are **pinned to one Python version** and drift as newer Pythons add
    builtins/`math` functions. A doctest holding a long match list will break on a Python upgrade —
    so prefer doctest examples whose expected output is **short and version-stable** (e.g.
    `methodfinder.find([1,2,3]) == 6` style, a boolean/scalar), and keep the long,
    version-sensitive exact-list assertions as `unittest` (where "regenerate the block" is already
    the documented maintenance step).

## Criteria — doctest vs stays unittest

- **Doctest:** short, deterministic, version-stable `example → result` that documents a feature.
- **Keep unittest:** the long exact-match-list assertions that drift across Python versions; the
  numpy case if its repr is fragile; anything needing a debugger to understand.

## Plan

1. (Blocked on the template task giving a `make test`.) Decide the runner: pytest with
   `--doctest-modules` over `methodfinder.py` is the template-consistent choice and subsumes the
   existing `doctest.testmod` case.
2. Migrate the version-stable example cases into `methodfinder.py` docstrings; keep the fragile
   exact-list ones as unittest (or as doctests with a regenerate note, maintainer's call).
3. Wire doctests into `make test`; drop the now-redundant `test_doctest` wrapper if pytest collects
   doctests directly.
4. Green gate; confirm the migrated examples ran.

## Notes

Part of a cross-repo "doctests by default" initiative. The shared convention + lessons now live in
**`~/.claude/reference/doctests-by-default.md`** (canonical: github.com/billsix/runClaudeInContainer;
read its `## Python` section first — it covers the `--doctest-modules` wiring, the hyphen-filename
discoverability issue (directly relevant here), the consolidation hazards, and the keep-as-pytest
exceptions).

**Required on completion:** append anything new this migration taught to `doctests-by-default.md`
(its `## Python` section, or the language-agnostic core if general) and re-sync the byte-identical
runCrush mirror (`runCrushInContainer tasks/reference/doctests-by-default.md`).
