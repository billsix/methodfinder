# Deep study of the source, with behavior-preserving change recommendations

**Status:** done 2026-11-02 — the high-confidence behavior-preserving subset was applied and
verified (staged, not committed); larger/behavior-changing items are deferred to
[[refactor-methodfinder-deferred]]. Archive owed after the maintainer's work commit.
**Priority:** 5
**Difficulty:** 5
**Created:** 2026-11-02 (William Emerison Six <billsix@gmail.com>)
**Updated:** 2026-11-02 (William Emerison Six <billsix@gmail.com>)

## BLUF

Read `src/methodfinder/methodfinder.py` in depth and produce a reviewed list of
**behavior-preserving** change recommendations — refactors, clarifications, and structural
simplifications that leave the program's **observable output byte-identical for every input** on a
fixed interpreter. "Done" = each recommendation is written up in this doc with rationale, the
risk that it changes behavior, and how that risk is checked, and **nothing is applied** — applying
is a separate go-ahead (see Open questions). This is a study/recommendation task, not an edit task.

## Context (cold start)

- **What the code is:** one ~390-line module, `src/methodfinder/methodfinder.py`. `find(*objects)`
  returns a `_Foo` wrapper whose overloaded `__eq__` runs the search and **prints** each matching
  call, sorted + de-duplicated. The un-sugared entry point is `_find(objects, expected_value)`.
  Read the three reference docs first — they already map the design and are accurate as of
  2026-11-02:
  - `tasks/reference/architecture-overview.md` — layout, entry points, what it is.
  - `tasks/reference/find-algorithm.md` — the `==` DSL, permutations + deepcopy, the builtins
    sweep, the attribute sweep, nested/type-strict equality, operator-vs-method pretty-printing,
    and the live-vs-dead-code note.
  - `tasks/reference/tests-and-packaging.md` — the 16-case suite, how it runs, Python-version drift.
- **Style is already done — do NOT re-propose it.** The container-adoption task already brought
  this module fully to the house standard (ruff `E`/`F`/`I` + `ty` + annotate-every-binding, all
  green; dead imports/typo removed, `type == type`→`is`, `not in`, redundant `cast` dropped,
  ambiguous `l`→`args`). ruff/`ty` own formatting, imports, and naming casing. This task is about
  **semantics and structure** the linters can't see, not a second style pass.
- **Hard behavior invariants this study must NOT recommend away** (each is load-bearing; changing
  any of them changes output and is therefore out of scope for a *behavior-preserving* change):
  - The three bare `except:` clauses (carry `# noqa: E722`). They must swallow **any**
    `BaseException` — the builtins sweep probes `exit()`/`quit()`, which raise `SystemExit`.
    `except Exception:` is **wrong** and was already proven to break `find`. Do not touch them.
  - The `==`-returns-`None` DSL, the `redirect_stdout/stderr` to devnull, the auto-injection of
    `itertools`/`functools`/`math` when no module is passed, the deepcopy-per-permutation mutation
    guard (modules/strings passed uncopied), the `type(o1) is type(o2)` bool-coercion block, the
    first-100-element cap in nested equality, the dunder allow-list, the `__r*__`-dropping and
    `infix_builtins` operator rendering in the pretty-printer, and the final `sorted(set(...))`.
  - Observable output is **interpreter-version-sensitive** (it enumerates whatever the running
    Python exposes). "Behavior-preserving" is therefore defined against a **fixed interpreter — the
    container's Python 3.14** — not across versions.

## Plan (on go-ahead — do NOT execute yet)

1. **Build the differential oracle first** (before proposing anything). The 16-case suite is too
   small to certify behavior preservation on its own. Write an adhoc harness
   (`tasks/adhoc/study-source-behavior-preserving-recommendations/diff_output.py`) that runs a
   broad battery of `_find(...)`/`find(...)==...` queries (the test cases plus many more: ints,
   floats, strings, lists, tuples, dicts, sets, numpy arrays, 1/2/3-arg forms, module-passed forms)
   and captures the exact printed output. Run it on the **current** committed code in-container to
   snapshot the baseline. This is the mechanical "before" the convention requires
   (`~/.claude/reference/porting-with-an-output-oracle.md`), not a hand-transcribed one.
2. **Read the module in depth** against the reference docs, through the house lenses that linters
   can't check: named recursion schemes / map-filter-fold
   (`~/.claude/reference/recursive-design.md`), total dispatch over open conditionals, extract-a-
   function criteria, expression-vs-mutate (`~/.claude/reference/code-style-conventions.md`,
   `~/.claude/reference/python-coding-standard.md`). Distinguish **true behavior-preserving**
   candidates from anything that would shift output.
3. **Write each recommendation into this doc** (a `## Findings` section), one per item:
   what + where (function + anchor), why it's clearer/better, the **behavior-preservation risk**
   (does it touch any invariant above?), and the harness result proving output is unchanged. Rank
   by value/safety. Explicitly list any tempting change that is **not** behavior-preserving and is
   therefore excluded.
4. **Verify** every proposed change against the oracle: apply it on a scratch branch/copy, re-run
   the harness, and confirm the diff vs the baseline snapshot is **empty**, plus `make test`
   (16/16) and `make format`/`make type-check` stay green. A recommendation with a non-empty diff
   is reclassified as behavior-changing and dropped from this task.
5. At archive, harvest any durable design insight into `find-algorithm.md`; promote the harness to
   `tools/` only if it earns reuse (else `git rm` it with the archive commit).

## Decided (William Emerison Six <billsix@gmail.com>, 2026-11-02)

"Do everything you think is reasonable and you recommend, and make a follow-up task for anything
else, including behavior-changing." → applied the high-confidence behavior-preserving subset
(below) and deferred the rest (larger behavior-preserving refactors + all behavior-changing ideas)
to [[refactor-methodfinder-deferred]].

## Findings & outcome (2026-11-02)

**Method.** Built the differential oracle first
(`tasks/adhoc/study-source-behavior-preserving-recommendations/diff_output.py`): a 34-query battery
(the 16 test inputs + many more — every sweep, operator, value-attribute, `__contains__`, prefix/
infix rendering, the bool-coercion block, nested-iterable equality, permutations, the numpy path).
Snapshotted `data/baseline.txt` on the committed code, applied the subset, snapshotted
`data/candidate.txt`, and diffed: **byte-identical across all 34 cases**. Gates after: `make format`
exit 0, `make type-check` exit 0, `make test` **16/16 OK** (container Python 3.14.8).

**Applied — behavior-preserving (all verified by the empty diff):**
1. `find(*objects: Iterable[object])` → `*objects: object` — the old annotation wrongly claimed
   every argument is iterable (you call `find(0)`); `*args` annotates the element type.
2. Dropped redundant `.keys()` from three `in` membership tests (`x in d`, not `x in d.keys()`).
3. `attribute_name == "lookfor" or attribute_name == "info"` → `in ("lookfor", "info")`.
4. `argList` → `arg_list` (house snake_case; the file already used `arg_list_to_print` elsewhere).
   Not caught by ruff because `select` is only `E`/`F`/`I` (no `N`).
5. `list(sorted(set(...)))` → `sorted(set(...))` at both sites — `sorted` already returns a list.
6. `Union[str, None]` → `str | None` (two sites) and dropped the now-unused `Union` import.
7. Annotated the lone unannotated nested def: `attribute_should_be_tested(att: str) -> bool`.
8. `_Foo.objects` annotation `Iterable[object]` → `list[object]` (it's assigned `list(objects)`).
9. `if result:` → `if result is not None:` — matches the `str | None` contract; proven equivalent
   because `_pretty_print_results` never returns `""` (harness diff empty).
10. Flattened the two nested `with open(os.devnull) as f …` blocks (which shadowed `f`) into one
    parenthesized `with` with distinct `out`/`err` names — one less indent level.

**Explicitly NOT touched** (would change output or are load-bearing): the three bare `except:`
(SystemExit-swallowing), the `==`-returns-`None` DSL, the devnull redirect, the default-module
auto-injection, the deepcopy-per-permutation guard, `type(o1) is type(o2)`, the 100-element cap,
the dunder allow-list, the `__r*__`-dropping + `infix_builtins` rendering, and `sorted(set(...))`.
The `_find`/`__eq__` double `sorted(set(...))` was checked and is **not** redundant — the outer one
merges + dedups across the base call and the three default-module calls.

**Harness disposition:** promoted to `tools/behavior_diff.py` (the reusable behavior oracle; the
transient `data/` snapshot was `git rm`'d with this archive). The follow-on refactors in
[[refactor-methodfinder-deferred]] reuse it.
