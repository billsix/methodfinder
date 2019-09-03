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

import itertools
import copy
import builtins
import itertools
import functools
import math
import contextlib
import inspect
import os


def find(*objects):
    """Sometimes you know the inputs and outputs for a procedure, but you don't remember the name.
    methodfinder.find tries to find the name.

    >>> import methodfinder
    >>> import itertools
    >>> methodfinder.find([1,2,3]) == 6
    sum([1, 2, 3])
    >>> methodfinder.find('1 + 1') == 2
    eval('1 + 1')
    >>> methodfinder.find(0.0) == 1.0
    math.cos(0.0)
    math.cosh(0.0)
    math.erfc(0.0)
    math.exp(0.0)
    >>> methodfinder.find(0) == 1
    0.denominator
    math.factorial(0)
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
    sum([1, 2, 3])

"""

    def __init__(self, objects):
        self.objects = objects

    def __eq__(self, other):
        """
        Find the methods calls that match, including any functions on
        itertools or functools
"""
        def toOutput():
            yield from _find(self.objects, expected_value=other)
            default_modules = [itertools, functools, math]
            # this if statement is a hack.  I need to actually figure out why first
            # object and rest objects end up being the same if the empty list
            # is passed to methodfinder
            if self.objects != ([],):
                for m in default_modules:
                    yield from _find(([m]+list(self.objects)), expected_value=other)


        for x in list(sorted(set(toOutput()))): print(x)

        # do not return True or False.  Nobody should be using this method
        # to actually test for equality.  This is only for nice syntax
        # for methodfinding.
        return


def _find(objects, expected_value):
    # remove the duplicates by putting the iterator into a set, and then
    # sort the unique results, for the purpose of deterministic outputs
    # for unit testing
    return list(sorted(set(__find(objects, expected_value))))


# the main procedure.  Find any method calls on all objects, and syntax, which
# results in the arguments evaluating to the desired result.
# returns an iterator of strings, which when evaluated, equal the result.
# This iterator may contain duplicates, which need to be removed
def __find(objects, expected_value):
    # get all permutations of the argument list.
    # deep copy each argument to protect against accidental mutation
    # by attribute calls
    for first_object, *rest_objects in list(_permutations(objects)):

        # test if any of the builtin functions, when applied to the arguments
        # evaluate to the desired result.
        # not every builtin function should be called.  print and input
        # do IO, and breakpoint invokes the debugger.
        # But all other builtin fns need to be tested
        for fn in filter(lambda x: not x in ['print', 'input', 'breakpoint', 'exec', 'open', 'help'],
                         dir(builtins)):
            # because the builtin procedures may take a different number
            # of arguments than provided, or the types may not match
            # the expected types, exceptions will frequently be thrown
            # rather than having large try/except blocks which just pass
            # in the body of the exception handler, use contextlib
            # to auto pass on exceptions
            with contextlib.suppress(*_errors_to_ignore):
                # get the builtin procedure, apply it to the arguments,
                # and test if the result is the desired result

                argList = ([first_object] + rest_objects)
                if _test_for_equality_nestedly_and_block_implicit_bool_conversion(getattr(builtins, fn)(*argList),
                                                                                  expected_value):
                    yield fn + "(" + _repr_arg_list(argList) + ")"

        # test if any of the attributes, when applied to the arguments
        # evaluate to the desired result

        # get the name of each attribute of the first object, and the associated
        # procedure.
        for attribute_name, attribute in [(d, getattr(first_object, d)) for d in dir(first_object)]:
            # getting the attribute doesn't always return a function as a value of the attribute
            # sometimes it returns a non function value.
            # test to see if that value is the desired result
            if _test_for_equality_nestedly_and_block_implicit_bool_conversion(attribute, expected_value):
                yield _repr(first_object)+"."+attribute_name
            # if the attribute is a procedure
            elif callable(attribute):
                # test if the application of the attribute procedure to the argument list
                # evaluates to the desired result

                # Rather than using a large try/except block, in which the except block would
                # just pass, use contextlib.suppress catch exceptions, and auto-pass
                with contextlib.suppress(*_errors_to_ignore):
                    # evaulate the application the attribute procedure to the remaining arguments, test if
                    # if equals the desired result.
                    if _test_for_equality_nestedly_and_block_implicit_bool_conversion(attribute(*rest_objects), expected_value):
                        result = _pretty_print_results(
                            expected_value, first_object, rest_objects, attribute, attribute_name)
                        # if the returned value is not None, then we found a match!
                        if result:
                            yield result


def _permutations(objs):
    """Return a list of permutations, all of which are deep copied
"""
    def deep_copy_iterator(perm):
        for o in perm:
            if inspect.ismodule(o) or isinstance(o, str):
                yield o
            else:
                yield copy.deepcopy(o)
    for perm in itertools.permutations(objs):
        yield deep_copy_iterator(perm)



def _test_for_equality_nestedly_and_block_implicit_bool_conversion(o1, o2):
    """test objects, or sequences, for equality. sequences are tested recursively.  Block
    implicit conversion of values to bools.

    >>> import methodfinder
    >>> methodfinder._test_for_equality_nestedly_and_block_implicit_bool_conversion(1,1)
    True
    >>> methodfinder._test_for_equality_nestedly_and_block_implicit_bool_conversion(1,2)
    False
    >>> methodfinder._test_for_equality_nestedly_and_block_implicit_bool_conversion([1,2,3],[1,2,3])
    True
    >>> methodfinder._test_for_equality_nestedly_and_block_implicit_bool_conversion([1,2,3],[2,1,3])
    False
    >>> methodfinder._test_for_equality_nestedly_and_block_implicit_bool_conversion(1,True)
    False
"""
    try:
        # if they have iterators, no exception will be thrown

        # take 100 elements from them.  any user of methodfinder
        # will not be putting in more than 100 elements
        # if it's not an iterator, an exception will be thrown
        for e1, e2 in itertools.zip_longest(itertools.islice(o1, 100),
                                            itertools.islice(o2, 100)):
            if not _test_for_equality_nestedly_and_block_implicit_bool_conversion(e1, e2):
                return False
        return True
    except:
        # since at least one of the objects does not have an iterator,
        # just test for equality normally.
        # test that the types are the same to suppress implicit
        # conversion of values to bools, which returns
        # way too many useless results for the purpose of methodfinder
        return (o1 == o2) and (type(o1) == type(o2))


def _pretty_print_results(expected_value, first_object, rest_objects, attribute, attribute_name):
    # if only a single object
    if not rest_objects:
        # these procedures are already tested by the builtin
        # procedures, so no need to print them out twice,
        # nor format them specially
        to_skip = {"__abs__": "abs",
                   "__bool__": "bool",
                   "__repr__": "repr",
                   "__str__": "str",
                   "__len__": "len",
                   }
        prefix_syntax = {"__neg__": "-",
                         }
        if attribute_name in prefix_syntax.keys():
            return prefix_syntax[attribute_name] + "(" + _repr(first_object) + ")"
        elif attribute_name not in to_skip.keys():
            return _repr(first_object)+"." + attribute_name+"()"
    # if there are more than 1 argument
    else:
        if attribute_name == "__contains__":
            return _repr_arg_list(rest_objects) + " in " + _repr(first_object) + os.linesep \
                + _repr(first_object) + ".__contains__(" + \
                _repr_arg_list(rest_objects) + ")"
        # don't bother testing the r methods.  They have equivalent
        # procedures where the inputs are reversed, which are already
        # testing because of the call to permutations.
        to_skip = ["__rmod__",
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
        if attribute_name in to_skip:
            return
        # rather than printing out the method calls
        # for double underscore methods, instead print the
        # syntax that implicitly calls these methods
        infix_builtins = {"__add__": "+",
                          "__mod__": "%",
                          "__sub__": '-',
                          "__mul__": '*',
                          "__truediv__": '/',
                          "__or__": '|',
                          "__xor__": '^',
                          "__and__": '&',
                          "__eq__": "==",
                          "__le__": "<=",
                          "__ge__": ">=",
                          "__pow__": "**",
                          "__floordiv__": "//",
                          }

        arg_list_to_print = _repr_arg_list(rest_objects)
        if attribute_name in infix_builtins.keys():
            return _repr(first_object) + infix_builtins[attribute_name] + arg_list_to_print
        else:
            return _repr(first_object) + "." + attribute_name + "(" + arg_list_to_print + ")"


def _repr(o):
    if inspect.ismodule(o):
        return o.__name__
    else:
        return repr(o)


def _repr_arg_list(l):
    """pretty print a list of arguments

    >>> import methodfinder
    >>> methodfinder._repr_arg_list([1,2,3,'4'])
    "1, 2, 3, '4'"
"""
    return ", ".join(map(_repr, l))


# the list of errors which can occur, which need to be suppressed.
# these errors can occur because we may be calling a procedure with the
# wrong number of arguments, the wrong types, etc.
_errors_to_ignore = [TypeError, ValueError, SystemExit,
                     OSError, IndexError, ModuleNotFoundError, AttributeError]
