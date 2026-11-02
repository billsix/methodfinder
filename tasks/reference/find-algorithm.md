# The find algorithm and the `==` DSL

All line references are to `src/methodfinder/methodfinder.py` unless noted. **Top-level
function anchors were refreshed after the 2026-11-02 refactor (which split the old `__find`
into `_find_impl` plus the two phase helpers `_builtins_sweep` / `_attribute_sweep`); the
finer intra-function line ranges are approximate — trust the function names over the exact
numbers.**

## The DSL: why `==` and not an argument

`find` never receives the expected result directly. The flow is:

1. `find(*objects)` (`methodfinder.py:33`) just wraps its arguments:
   `return _Foo(objects)`. `_Foo.__init__` (`:81`) stores them as a list.
2. Writing `== <expected>` invokes `_Foo.__eq__(self, other)` (`:84`), where `other` is
   the expected result. That method runs the whole search and **prints** each match, one
   per line, sorted and de-duplicated (`:106`).
3. `__eq__` deliberately returns `None`, never a bool (`:109-112`, with the comment "do
   not return True or False. Nobody should be using this method to actually test for
   equality"). The `==` exists only to give the query a natural reading:
   `find(x) == wanted`.

`_Foo.__eq__` also wraps the search in `contextlib.redirect_stdout`/`redirect_stderr` to
`os.devnull` (`:92-97`) because probing numpy attributes can spew text to stdout; that
noise is suppressed so the printed matches stay clean.

**Default extra modules.** If none of the supplied objects is itself a module, `__eq__`
re-runs the search with `itertools`, `functools`, and `math` prepended to the arguments
(`:99-104`). That is why `find([1,2,3]) == 6` finds `math.prod(...)` and
`find([1,2]) == [[1,2],[2,1]]` finds `itertools.permutations(...)` without you naming the
module. If you *do* pass a module (e.g. `find(np, 3) == ...`), the auto-injection is
skipped and only your module is searched.

## The search core

`_find(objects, expected_value)` (`:116`) is the testable entry point — it takes the
expected value as a plain argument, calls `_find_impl`, and returns `sorted(set(...))` so
results are unique and deterministic. `_find_impl` (`:129`) is a generator that, for each
**permutation** of the argument objects, delegates to two phase helpers (and may yield
duplicates):

### 1. Builtins sweep — `_builtins_sweep` (`:144`)

Iterates `dir(builtins)`, skipping the ones that would do I/O, mutate state, or hang:
`print`, `input`, `breakpoint`, `exec`, `open`, `help` (the `_BUILTINS_TO_SKIP` constant at
`:141`). Each remaining builtin is called with the full permuted argument list inside a bare
`try/except: pass` — most calls raise `TypeError` for wrong arity/types, and those are
silently discarded. A call whose result passes the equality test yields `fn(arg, arg, ...)`.

### 2. Attribute sweep — `_attribute_sweep` (`:204`)

For the **first** object of the permutation, it walks `dir(first_object)` filtered by
`_attribute_should_be_tested` (`:161`): public names (not starting with `_`) **plus** an
explicit allow-list of the operator and protocol dunders worth finding — the arithmetic/
bitwise set (`__add__`, `__mod__`, `__truediv__`, …), the full comparison set
(`__lt__`/`__le__`/`__gt__`/`__ge__`/`__eq__`/`__ne__`), the protocol methods
(`__contains__`, `__len__`, `__neg__`, `__abs__`, …), and the reflected `__radd__` family.
numpy's `lookfor` and `info` attributes are explicitly skipped because probing them is
noisy/slow.

Each surviving attribute is handled two ways:

- **Value attribute**: the attribute's *value* itself is compared to the expected result —
  this is how `0.denominator`, `1.numerator`, `(1).real` are found.
- **Callable attribute**: the attribute is called with the *remaining* arguments
  (`attribute(*rest_objects)`), again under `try/except: pass`, and a matching result is
  handed to `_pretty_print_results` for formatting.

## Equality: nested and type-strict

`_test_for_equality_nestedly_and_block_implicit_bool_conversion(o1, o2)` (`:262`) is the
gate every candidate must pass. Two deliberate behaviors:

- **Recurses into iterables** (`:260-277`): if both operands are iterable it compares them
  element-by-element (via `zip_longest`), recursively, taking at most the first 100
  elements of each (`:271`, comment: nobody methodfinding will use more than 100). This is
  why the expected result can be written as a nested list even when the real return is an
  iterator or a numpy array.
- **Blocks implicit bool coercion**: for the scalar base case it requires
  `type(o1) is type(o2)` *and* `o1 == o2` (the `is` tightened from `==` in the 2026-11-02
  cleanup — exact-type identity, same behavior). Without the type check, `1 == True` and
  `0 == False` would flood the output with useless matches. This is why
  `find(1,1) == 1` does **not** list every truthy path, and why the docstring test
  `..._block_implicit_bool_conversion(1, True)` returns `False` (`:258`).

## Permutations and mutation safety

`_permutations` (`:248`) yields every ordering of the arguments (via
`itertools.permutations`) and **deep-copies** each argument as it goes (`:232-237`), so an
attribute call that mutates its receiver (e.g. `list.sort`) cannot corrupt the objects for
later candidates. Modules and strings are passed through uncopied (`:234`) — modules
aren't deep-copyable and strings are immutable. Permuting the arguments is also what lets
the reflected operators be reached from the plain ones, which is why the `__r*__` methods
are skipped in the pretty-printer (see below).

## Pretty-printing results

`_pretty_print_results` (`:307`) turns a match into the string the user sees, choosing a
representation that mirrors how a Python programmer would actually write the call:

- **Single argument**: dunders already covered by a builtin are skipped so they aren't
  printed twice — `__abs__`/`__bool__`/`__repr__`/`__str__`/`__len__` map to
  `abs`/`bool`/`repr`/`str`/`len`. `__neg__` is rendered as prefix `-(x)`. Everything else
  prints as `x.name()`.
- **Multiple arguments**: `__contains__` becomes the `in` syntax and appends the hint
  comment about overriding `__contains__`. The reflected `__r*__` methods are dropped
  entirely because the permutation pass already found their non-reflected equivalents. The
  remaining infix operator dunders are rendered as real operators via the `infix_builtins`
  map — `__add__`→`+`, `__truediv__`→`/`, `__pow__`→`**`, the comparisons
  `__lt__`/`__le__`/`__gt__`/`__ge__`/`__eq__`/`__ne__`→`<`/`<=`/`>`/`>=`/`==`/`!=`, etc. —
  so you see `3/2` or `3<4`, not `(3).__truediv__(2)`.

`_repr` (`:397`) prints a module by its `__name__` (so `numpy`, not the repr of the module
object) and everything else via `repr` (`inspect.ismodule` narrows the type, so no explicit
`cast` is needed). `_repr_arg_list` (`:405`) joins arguments with `", "`.

## Live vs. dead code

Everything in this file is live and reachable from `find`/`_find`; there is no vestigial
code. The names are `find`, `_Foo`, `_find`, `_find_impl`, the two phase helpers
`_builtins_sweep` / `_attribute_sweep`, the `_attribute_should_be_tested` filter, and the
`_pretty_print_results` / `_repr` / `_repr_arg_list` / `_permutations` /
`_test_for_equality_nestedly_and_block_implicit_bool_conversion` helpers. The three bare
`except:` clauses are deliberate — they must swallow *any* `BaseException` from probing
arbitrary callables, e.g. `exit()` raising `SystemExit` — and each carries a narrow
`# noqa: E722` with that reason.
