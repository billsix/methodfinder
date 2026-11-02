# methodfinder refactors deferred from the source study — larger & behavior-changing

**Status:** done 2026-11-02 — applied A1+A2+B7 (behavior-preserving) and B5 (the comparison
operators, behavior-changing); declined B3/B4/B6. Verified and committed (behavior-preserving +
behavior-changing commits); archived 2026-11-02.
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
- **Reuse the behavior oracle.** `tools/behavior_diff.py` snapshots `find`'s output over a 34-query
  battery (run it before a change and after, then `diff`). For a **behavior-preserving** item the
  before↔after diff must be **empty**; for a **behavior-changing** item the diff is the *expected*
  delta — review it line-by-line and regenerate the expected-output docstrings/README to match.
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
   `eval('1 + 1')`; `exec`/`open`/`input`/etc. are excluded but `eval` is not. Options: **(a)** keep
   probing `eval` (status quo — the `eval('1 + 1')` doctest answer stays); **(b)** exclude `eval`
   too (drop that answer and regenerate the doctest). No recommendation — your call on whether
   `eval` is a wanted answer.
4. **The builtins exclusion list is minimal** (`print input breakpoint exec open help`). Many
   builtins that mutate/do-IO/exit are still probed and survive only via the bare `except:`
   (`exit`/`quit` → `SystemExit`). Options: **(a)** leave as-is — the bare `except:` absorbing them
   is the deliberate design; **(b)** curate an explicit safe-builtins allow/deny policy (changes
   which calls are attempted, possibly the output). Recommend **(a)**.
5. **The dunder allow-list in `attribute_should_be_tested` is incomplete** — it omits e.g.
   `__divmod__`, `__matmul__` (`@`), `__lshift__`/`__rshift__` (`<<`/`>>`), `__invert__` (`~`),
   `__lt__`/`__gt__`/`__ne__`. Each addition makes `find` discover more operators (more output).
   Options: **(a)** leave the list as-is; **(b)** add specified operators (say which) **and** their
   renderings in `_pretty_print_results`. No default — depends which operators you want findable.
6. **`_Foo.__eq__` is annotated `-> Any` but always returns `None`.** Options: **(a)** leave
   `-> Any`; **(b)** change to `-> None` **iff** `ty` stays green (base `object.__eq__` is `-> bool`,
   so verify the override check first, fall back to (a) if ty complains). Type-surface change only,
   not runtime. Recommend trying **(b)**, fall back to **(a)**.
7. **Module-level `__find` / `_Foo` naming.** `__find` is a double-underscore module function (no
   mangling at module scope). Options: **(a)** leave; **(b)** rename (e.g. `__find`→`_find_impl`) —
   a (private) API rename, only worth doing bundled with item 1. Recommend **(a)** unless you take
   item 1.

## Outcome (William Emerison Six <billsix@gmail.com>, 2026-11-02)

Done at the maintainer's "do everything you think should be done." Verified with
`tools/behavior_diff.py` (34-query battery): the A-bundle diff vs baseline was **empty**
(behavior-preserving); the B5 diff was the single expected delta (below). `make format` /
`type-check` / `test` (16/16) all green on Python 3.14.8.

**Applied:**
- **A1 — extracted the sweeps.** `__find` → `_find_impl`, which now does `yield from
  _builtins_sweep(...)` then `yield from _attribute_sweep(...)` per permutation; the dunder filter
  became the module-level `_attribute_should_be_tested`, and the builtins skip-list the
  `_BUILTINS_TO_SKIP` constant.
- **A2 — modernized imports.** `typing.Iterable` → `collections.abc.Iterable`.
- **B7 — renamed** the module-level `__find` → `_find_impl` (as part of A1).
- **B5 — added the comparison operators** `__lt__`/`__gt__`/`__ne__` to the allow-list and
  `<`/`>`/`!=` to `infix_builtins`. Only observable effect in the battery: `find('abc','b') == True`
  now also yields `'abc'<'b'`, `'abc'!='b'`, `'b'>'abc'`, `'b'!='abc'` (filling the `<`/`>`/`!=`
  symmetry alongside the pre-existing `<=`/`>=`/`==`). No unit test or doctest has a same-type
  bool-expected comparison case, so none needed regenerating — the gate stayed green.

**Declined (behavior kept as-is):**
- **B3** — keep probing `eval` (a valid, pure method-finder answer; it's doctested).
- **B4** — keep the minimal builtins exclusion list (the bare `except:` absorbing `exit`/`quit`/etc.
  is the deliberate design).
- **B6** — keep `_Foo.__eq__ -> Any` (`-> None` would be an incompatible `__eq__` override and trip
  `ty`).

Reference doc `find-algorithm.md` updated to the new structure + operators. The harness is the
promoted `tools/behavior_diff.py`. Archived 2026-11-02.
