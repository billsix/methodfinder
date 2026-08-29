# The find algorithm and the `==` DSL

All line references are to `src/methodfinder/methodfinder.py` unless noted.

## The DSL: why `==` and not an argument

`find` never receives the expected result directly. The flow is:

1. `find(*objects)` (`methodfinder.py:35`) just wraps its arguments:
   `return _Foo(objects)`. `_Foo.__init__` (`:76`) stores them as a list.
2. Writing `== <expected>` invokes `_Foo.__eq__(self, other)` (`:79`), where `other` is
   the expected result. That method runs the whole search and **prints** each match, one
   per line, sorted and de-duplicated (`:98`).
3. `__eq__` deliberately returns `None`, never a bool (`:101-104`, with the comment "do
   not return True or False. Nobody should be using this method to actually test for
   equality"). The `==` exists only to give the query a natural reading:
   `find(x) == wanted`.

`_Foo.__eq__` also wraps the search in `contextlib.redirect_stdout`/`redirect_stderr` to
`os.devnull` (`:88-89`) because probing numpy attributes can spew text to stdout; that
noise is suppressed so the printed matches stay clean.

**Default extra modules.** If none of the supplied objects is itself a module, `__eq__`
re-runs the search with `itertools`, `functools`, and `math` prepended to the arguments
(`:91-96`). That is why `find([1,2,3]) == 6` finds `math.prod(...)` and
`find([1,2]) == [[1,2],[2,1]]` finds `itertools.permutations(...)` without you naming the
module. If you *do* pass a module (e.g. `find(np, 3) == ...`), the auto-injection is
skipped and only your module is searched.

## The search core

`_find(objects, expected_value)` (`:107`) is the testable entry point — it takes the
expected value as a plain argument, calls `__find`, and returns
`list(sorted(set(...)))` so results are unique and deterministic. `__find` (`:118`) is a
generator that does the actual work and may yield duplicates.

For each **permutation** of the argument objects (`:122`), `__find` tries two families of
candidates:

### 1. Builtins sweep (`:128-145`)

Iterates `dir(builtins)`, skipping the ones that would do I/O, mutate state, or hang:
`print`, `input`, `breakpoint`, `exec`, `open`, `help` (the filter at `:128-131`). Each
remaining builtin is called with the full permuted argument list inside a bare
`try/except: pass` (`:135-145`) — most calls raise `TypeError` for wrong arity/types, and
those are silently discarded. A call whose result passes the equality test yields
`fn(arg, arg, ...)`.

### 2. Attribute sweep (`:149-226`)

For the **first** object of the permutation, it walks `dir(first_object)` filtered by
`attribute_should_be_tested` (`:149`): public names (not starting with `_`) **plus** an
explicit allow-list of ~35 dunders (`:151-184`) — the operator and protocol methods worth
finding (`__add__`, `__contains__`, `__len__`, `__neg__`, the reflected `__radd__` family,
etc.). numpy's `lookfor` and `info` attributes are explicitly skipped (`:193-196`) because
probing them is noisy/slow.

Each surviving attribute is handled two ways:

- **Value attribute** (`:200-203`): the attribute's *value* itself is compared to the
  expected result — this is how `0.denominator`, `1.numerator`, `(1).real` are found.
- **Callable attribute** (`:205-226`): the attribute is called with the *remaining*
  arguments (`attribute(*rest_objects)`), again under `try/except: pass`, and a matching
  result is handed to `_pretty_print_results` for formatting.

## Equality: nested and type-strict

`_test_for_equality_nestedly_and_block_implicit_bool_conversion(o1, o2)` (`:243`) is the
gate every candidate must pass. Two deliberate behaviors:

- **Recurses into iterables** (`:260-277`): if both operands are iterable it compares them
  element-by-element (via `zip_longest`), recursively, taking at most the first 100
  elements of each (`:271`, comment: nobody methodfinding will use more than 100). This is
  why the expected result can be written as a nested list even when the real return is an
  iterator or a numpy array.
- **Blocks implicit bool coercion** (`:284`): for the scalar base case it requires
  `type(o1) == type(o2)` *and* `o1 == o2`. Without the type check, `1 == True` and
  `0 == False` would flood the output with useless matches. This is why
  `find(1,1) == 1` does **not** list every truthy path, and why the docstring test
  `..._block_implicit_bool_conversion(1, True)` returns `False` (`:258`).

## Permutations and mutation safety

`_permutations` (`:229`) yields every ordering of the arguments (via
`itertools.permutations`) and **deep-copies** each argument as it goes (`:232-237`), so an
attribute call that mutates its receiver (e.g. `list.sort`) cannot corrupt the objects for
later candidates. Modules and strings are passed through uncopied (`:234`) — modules
aren't deep-copyable and strings are immutable. Permuting the arguments is also what lets
the reflected operators be reached from the plain ones, which is why the `__r*__` methods
are skipped in the pretty-printer (see below).

## Pretty-printing results

`_pretty_print_results` (`:287`) turns a match into the string the user sees, choosing a
representation that mirrors how a Python programmer would actually write the call:

- **Single argument** (`:295-310`): dunders already covered by a builtin are skipped so
  they aren't printed twice — `__abs__`/`__bool__`/`__repr__`/`__str__`/`__len__` map to
  `abs`/`bool`/`repr`/`str`/`len` (`:299-305`). `__neg__` is rendered as prefix `-(x)`
  (`:306-308`). Everything else prints as `x.name()`.
- **Multiple arguments** (`:312-370`): `__contains__` becomes the `in` syntax and appends
  the hint comment about overriding `__contains__` (`:313-320`). The reflected
  `__r*__` methods are dropped entirely (`:324-337`) because the permutation pass already
  found their non-reflected equivalents. The remaining infix operator dunders are rendered
  as real operators via the `infix_builtins` map (`:341-355`) — `__add__`→`+`, `__mod__`→
  `%`, `__truediv__`→`/`, `__pow__`→`**`, `__floordiv__`→`//`, etc. — so you see `3/2`, not
  `(3).__truediv__(2)`.

`_repr` (`:374`) prints a module by its `__name__` (so `numpy`, not the repr of the module
object) and everything else via `repr`. `_repr_arg_list` (`:382`) joins arguments with
`", "`.

## Live vs. dead code

Everything in this file is live and reachable from `find`/`_find`; there is no vestigial
code. Confirmed by reading the single module top to bottom — the only names are `find`,
`_Foo`, `_find`, `__find`, and the six `_`-prefixed helpers, and each is called by the one
above it. Minor cosmetic issues (not bugs): `import itertools` appears twice
(`methodfinder.py:21` and `:24`), and there is a typo "writcten" in a comment at `:86`.
