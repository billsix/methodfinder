# Copyright (c) 2019 William Emerison Six
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import builtins
import contextlib
import copy
import functools
import inspect
import itertools
import math
import os
from collections.abc import Iterable
from typing import Any, cast


def find(*objects: object) -> "_Foo":
    """Sometimes you know the inputs and outputs for a procedure, but you don't
    remember the name. methodfinder.find tries to find the name.

    The expected-output lists below are pinned to the dev container's Python
    (3.14); newer interpreters add builtins/math functions, so a failing line
    usually means "regenerate this block", not an algorithm bug.

    >>> import methodfinder
    >>> import itertools
    >>> methodfinder.find([1,2,3]) == 6
    math.prod([1, 2, 3])
    sum([1, 2, 3])
    >>> methodfinder.find('1 + 1') == 2
    eval('1 + 1')
    >>> methodfinder.find(0.0) == 1.0
    math.cos(0.0)
    math.cosh(0.0)
    math.erfc(0.0)
    math.exp(0.0)
    math.exp2(0.0)
    >>> methodfinder.find(0) == 1
    0.denominator
    math.factorial(0)
    math.perm(0)
    >>> import numpy as np
    >>> methodfinder.find(np, 3) == np.array(
    ...     [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    ... )
    numpy.eye(3)
    numpy.identity(3)
    """
    # Just call the wrapper function so that the == sign can be used to specify
    # the desired result
    return _Foo(objects)


class _Foo:
    """
    Wrapper class for testing methodfinders results via ==

    >>> import methodfinder
    >>> import itertools
    >>> methodfinder.find([1,2,3]) == 6
    math.prod([1, 2, 3])
    sum([1, 2, 3])
    """

    def __init__(self, objects: Iterable[object]) -> None:
        self.objects: list[object] = list(objects)

    def __eq__(self, other: Any) -> Any:
        """
        Find the methods calls that match, including any functions on
        itertools or functools"""

        def to_output() -> Iterable[str]:
            # for some reason, when querying numpy procedures,
            # some results are written to standard out
            # suppress that for the purposes of the doctests
            with (
                open(os.devnull, "w") as out,
                contextlib.redirect_stdout(out),
                open(os.devnull, "w") as err,
                contextlib.redirect_stderr(err),
            ):
                yield from _find(self.objects, expected_value=other)
                if not any(map(inspect.ismodule, self.objects)):
                    default_modules: Iterable[object] = [itertools, functools, math]
                    for m in default_modules:
                        yield from _find(
                            ([m] + list(self.objects)), expected_value=other
                        )

        for x in sorted(set(to_output())):
            print(x)

        # do not return True or False.  Nobody should be using this method
        # to actually test for equality.  This is only for nice syntax
        # for methodfinding.
        return


def _find(objects: Iterable[object], expected_value: object) -> Iterable[str]:
    # remove the duplicates by putting the iterator into a set, and then
    # sort the unique results, for the purpose of deterministic outputs
    # for unit testing
    return sorted(set(_find_impl(objects, expected_value)))


# the main procedure.  Find any method calls on all objects, and syntax, which
# results in the arguments evaluating to the desired result.
# returns an iterator of strings, which when evaluated, equal the result.
# This iterator may contain duplicates, which need to be removed.
# Each permutation is run through two phases: the builtins sweep and the
# attribute sweep.
def _find_impl(objects: Iterable[object], expected_value: object) -> Iterable[str]:
    # get all permutations of the argument list.
    # deep copy each argument to protect against accidental mutation
    # by attribute calls
    for first_object, *rest_objects in list(_permutations(objects)):
        yield from _builtins_sweep(first_object, rest_objects, expected_value)
        yield from _attribute_sweep(first_object, rest_objects, expected_value)


# not every builtin should be called: print and input do IO, open touches the
# filesystem, breakpoint invokes the debugger, exec/help are noisy. Every other
# builtin is worth testing.
_BUILTINS_TO_SKIP: list[str] = ["print", "input", "breakpoint", "exec", "open", "help"]


def _builtins_sweep(
    first_object: object, rest_objects: list[object], expected_value: object
) -> Iterable[str]:
    """Yield ``fn(args)`` for each builtin whose call equals the desired result."""
    for fn in filter(lambda x: x not in _BUILTINS_TO_SKIP, dir(builtins)):
        # the builtin may take a different number of arguments than provided, or
        # the types may not match, so calls frequently raise; discard those.
        try:
            arg_list: list[object] = [first_object] + rest_objects
            if _test_for_equality_nestedly_and_block_implicit_bool_conversion(
                getattr(builtins, fn)(*arg_list), expected_value
            ):
                yield fn + "(" + _repr_arg_list(arg_list) + ")"
        except:  # noqa: E722 -- must swallow SystemExit from probing exit()
            pass


def _attribute_should_be_tested(att: str) -> bool:
    # public names, plus an explicit allow-list of the operator/protocol dunders
    # worth finding.
    return not att.startswith("_") or (
        att
        in [
            "__abs__",
            "__add__",
            "__and__",
            "__bool__",
            "__contains__",
            "__eq__",
            "__floordiv__",
            "__ge__",
            "__le__",
            "__len__",
            "__mod__",
            "__mul__",
            "__neg__",
            "__or__",
            "__pow__",
            "__radd__",
            "__rand__",
            "__repr__",
            "__rfloordiv__",
            "__rmod__",
            "__rmul__",
            "__ror__",
            "__round__",
            "__rpow__",
            "__rtruediv__",
            "__rxor__",
            "__str__",
            "__sub__",
            "__truediv__",
            "__xor__",
        ]
    )


def _attribute_sweep(
    first_object: object, rest_objects: list[object], expected_value: object
) -> Iterable[str]:
    """Yield the matching attribute accesses / calls on ``first_object``."""
    # get the name of each attribute of the first object, and the associated
    # procedure.
    for attribute_name, attribute in [
        (d, getattr(first_object, d))
        for d in dir(first_object)
        if _attribute_should_be_tested(d)
    ]:
        if attribute_name in ("lookfor", "info"):  # numpy.lookfor and numpy.info
            continue
        # getting the attribute doesn't always return a function as its
        # value; sometimes it returns a non-function value. test to see if
        # that value is the desired result
        if _test_for_equality_nestedly_and_block_implicit_bool_conversion(
            attribute, expected_value
        ):
            yield _repr(first_object) + "." + attribute_name
        # if the attribute is a procedure
        elif callable(attribute):
            # test if applying the attribute procedure to the argument
            # list evaluates to the desired result
            try:
                # apply the attribute procedure to the remaining arguments
                # and test if it equals the desired result.
                if _test_for_equality_nestedly_and_block_implicit_bool_conversion(
                    attribute(*rest_objects), expected_value
                ):
                    result: str | None = _pretty_print_results(
                        expected_value,
                        first_object,
                        rest_objects,
                        attribute,
                        attribute_name,
                    )
                    # if the returned value is not None, then we found a match!
                    if result is not None:
                        yield result
            except:  # noqa: E722 -- must swallow SystemExit from probing exit()
                pass


def _permutations(objs: Iterable[object]) -> Iterable[Iterable[object]]:
    """Return a list of permutations, all of which are deep copied"""

    def deep_copy_iterator(perm: Iterable[object]) -> Iterable[object]:
        for o in perm:
            if inspect.ismodule(o) or isinstance(o, str):
                yield o
            else:
                yield copy.deepcopy(o)

    for perm in itertools.permutations(objs):
        yield deep_copy_iterator(perm)


def _test_for_equality_nestedly_and_block_implicit_bool_conversion(
    o1: object, o2: object
) -> bool:
    """Test objects, or sequences, for equality. Sequences are tested
    recursively. Blocks implicit conversion of values to bools.

    >>> import methodfinder
    >>> f = methodfinder._test_for_equality_nestedly_and_block_implicit_bool_conversion
    >>> f(1, 1)
    True
    >>> f(1, 2)
    False
    >>> f([1, 2, 3], [1, 2, 3])
    True
    >>> f([1, 2, 3], [2, 1, 3])
    False
    >>> f(1, True)
    False"""
    try:
        # if they have iterators, no exception will be thrown

        # take 100 elements from them.  any user of methodfinder
        # will not be putting in more than 100 elements
        # if it's not an iterator, an exception will be thrown

        o1_iter: Iterable[object] = cast(Iterable[object], o1)
        o2_iter: Iterable[object] = cast(Iterable[object], o2)

        for e1, e2 in itertools.zip_longest(
            itertools.islice(o1_iter, 100), itertools.islice(o2_iter, 100)
        ):
            if not _test_for_equality_nestedly_and_block_implicit_bool_conversion(
                e1, e2
            ):
                return False
        return True
    except:  # noqa: E722 -- must swallow SystemExit from probing exit()
        # since at least one of the objects does not have an iterator,
        # just test for equality normally.
        # test that the types are the same to suppress implicit
        # conversion of values to bools, which returns
        # way too many useless results for the purpose of methodfinder
        return (type(o1) is type(o2)) and (o1 == o2)


def _pretty_print_results(
    expected_value: object,
    first_object: object,
    rest_objects: list[object],
    attribute: object,
    attribute_name: str,
) -> str | None:
    # if only a single object
    if not rest_objects:
        # these procedures are already tested by the builtin
        # procedures, so no need to print them out twice,
        # nor format them specially
        to_skip_dict: dict[str, str] = {
            "__abs__": "abs",
            "__bool__": "bool",
            "__repr__": "repr",
            "__str__": "str",
            "__len__": "len",
        }
        prefix_syntax: dict[str, str] = {"__neg__": "-"}
        if attribute_name in prefix_syntax.keys():
            return prefix_syntax[attribute_name] + "(" + _repr(first_object) + ")"
        elif attribute_name not in to_skip_dict.keys():
            return _repr(first_object) + "." + attribute_name + "()"
    # if there are more than 1 argument
    else:
        if attribute_name == "__contains__":
            return (
                _repr_arg_list(rest_objects)
                + " in "
                + _repr(first_object)
                + os.linesep
                + '# to use the "in" syntax with your own type, override __contains__'
            )
        # don't bother testing the r methods.  They have equivalent
        # procedures where the inputs are reversed, which are already
        # testing because of the call to permutations.
        to_skip_list: list[str] = [
            "__rmod__",
            "__radd__",
            "__rtruediv__",
            "__ror__",
            "__rxor__",
            "__rand__",
            "__rfloordiv__",
            "__rmul__",
            "__round__",
            "__rpow__",
        ]
        if attribute_name in to_skip_list:
            return None
        # rather than printing out the method calls
        # for double underscore methods, instead print the
        # syntax that implicitly calls these methods
        infix_builtins: dict[str, str] = {
            "__add__": "+",
            "__mod__": "%",
            "__sub__": "-",
            "__mul__": "*",
            "__truediv__": "/",
            "__or__": "|",
            "__xor__": "^",
            "__and__": "&",
            "__eq__": "==",
            "__le__": "<=",
            "__ge__": ">=",
            "__pow__": "**",
            "__floordiv__": "//",
        }

        arg_list_to_print: str = _repr_arg_list(rest_objects)
        if attribute_name in infix_builtins.keys():
            return (
                _repr(first_object) + infix_builtins[attribute_name] + arg_list_to_print
            )
        else:
            return (
                _repr(first_object)
                + "."
                + attribute_name
                + "("
                + arg_list_to_print
                + ")"
            )
    return None


def _repr(o: object) -> str:
    # inspect.ismodule narrows `o` to ModuleType here (TypeIs), so no cast is needed.
    if inspect.ismodule(o):
        return o.__name__
    else:
        return repr(o)


def _repr_arg_list(args: Iterable[object]) -> str:
    """pretty print a list of arguments

    >>> import methodfinder
    >>> methodfinder._repr_arg_list([1,2,3,'4'])
    "1, 2, 3, '4'"
    """
    return ", ".join(map(_repr, args))
