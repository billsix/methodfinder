# methodfinder refactors deferred from the source study — larger & behavior-changing

**Status:** proposed — needs go-ahead (each item is independent; pick any subset).
**Priority:** 6
**Difficulty:** 5
**Created:** 2026-11-02 (William Emerison Six <billsix@gmail.com>)
**Updated:** 2026-11-02 (William Emerison Six <billsix@gmail.com>)

## BLUF

The in-depth source study ([[study-source-behavior-preserving-recommendations]], archived with its
findings) applied the high-confidence behavior-preserving tidies. This task holds the rest: the
**larger** behavior-preserving refactors (bigger diffs / churn the structure) and the
**behavior-changing** ideas (they alter what `find` prints). None is applied. "Done" per item =
either applied-and-verified, or explicitly rejected with a reason recorded. Each behavior-changing
item needs your decision first because it changes output.

## Context (cold start)

- Read [[study-source-behavior-preserving-recommendations]] (archived under
  `tasks/archive/2026/11/02/`) for the full method and the subset already applied, and the three
  reference docs under `tasks/reference/` for the design.
- **Reuse the behavior oracle.** The study's differential harness
  (`tasks/adhoc/study-source-behavior-preserving-recommendations/diff_output.py`; promote to
  `tools/` if this task proceeds) snapshots `find`'s output over a 34-query battery. For a
  **behavior-preserving** item the baseline↔candidate diff must be **empty**; for a
  **behavior-changing** item the diff is the *expected* delta and must be reviewed line-by-line and
  the expected-output docstrings/README regenerated to match.
- Output is interpreter-sensitive — verify on the container's Python 3.14, and remember the
  doctests are pinned to that interpreter.

## A. Behavior-preserving but larger (apply only with an empty oracle diff)

1. **Extract `__find`'s two sweeps into named generator helpers** — e.g. `_builtins_sweep(first,
   rest, expected)` and `_attribute_sweep(first, rest, expected)`, each a generator `__find` does
   `yield from`. The convention endorses *naming a distinct phase*; the cost is churn to the
   function's structure and to the line anchors in `tasks/reference/find-algorithm.md` (update them
   in the same change). Risk: it's a generator with load-bearing `try/except` and `yield` — keep the
   bare `except:` semantics exactly. (Recommended, medium effort.)
2. **Modernize the ABC imports:** `typing.Iterable` → `collections.abc.Iterable` throughout
   (`from collections.abc import Iterable`; keep `Any`/`cast` from `typing`). Mechanical, ~10 sites,
   behavior-preserving. Not enforced by ruff here (no `UP` in `select`). (Optional — pure style.)

## B. Behavior-changing (need a decision; each alters `find`'s output)

3. **Reconsider probing `eval` in the builtins sweep.** `find('1 + 1') == 2` currently yields
   `eval('1 + 1')`. `exec`/`open`/`input`/etc. are excluded but `eval` is not. Dropping `eval` would
   remove that (and is arguably safer/less surprising), but it changes documented output (a doctest
   asserts it). Decision: keep `eval` as a legitimate "method finder" answer, or exclude it?
4. **The builtins exclusion list is minimal** (`print input breakpoint exec open help`). Many
   builtins that mutate/do-IO/exit are still probed and only survive via the bare `except:`
   (`exit`/`quit` → `SystemExit`). A principled "safe builtins" allow/deny policy would change which
   calls are attempted and could change output. Decision: leave as-is (the bare except is the
   deliberate design), or curate the list?
5. **The dunder allow-list in `attribute_should_be_tested` is incomplete.** It omits e.g.
   `__divmod__`, `__matmul__` (`@`), `__lshift__`/`__rshift__` (`<<`/`>>`), `__invert__` (`~`),
   `__lt__`/`__gt__`/`__ne__`. Adding any makes `find` discover more operators (more output).
   Decision: which, if any, to add — and add the matching renderings to `_pretty_print_results`.
6. **`_Foo.__eq__` is annotated `-> Any` but always returns `None`.** Honest would be `-> None`, but
   that may trip `ty`'s `__eq__`-override signature check (base `object.__eq__ -> bool`). Treat as
   behavior-changing-to-the-type-surface: verify `ty` stays green before adopting, else leave.
7. **Module-level `__find` / `_Foo` naming.** `__find` is a double-underscore module function (no
   mangling at module scope). Renaming to `_find_impl` or similar is clearer but is a (private) API
   rename — only worth it bundled with item 1. Decision: leave, or rename alongside the extraction?

## Open questions (block implementation)

1. **Which items do you want done?** They're independent — answer by number (e.g. "1 and 2; skip
   the rest", or "all of A, hold B"). For any **B** item, also say the desired *direction* (e.g.
   "drop `eval`" vs "keep it"), since those change output and I can't pick for you.
