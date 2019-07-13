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
import contextlib


def find(*objects, whichEvaluatesTo):
    """Sometimes you know the inputs and outputs for a procedure, but you don't remember the name.
    methodfinder.find tries to find the name.

    >>> import methodfinder
    >>> import itertools
    >>> methodfinder.find([1,2,3], whichEvaluatesTo=6)
    sum([1, 2, 3])
    >>> methodfinder.find([1,2,6,7], 6, whichEvaluatesTo=True)
    6 in [1, 2, 6, 7]
    >>> methodfinder.find(" ",["foo", "bar"], whichEvaluatesTo="foo bar")
    ' '.join(['foo', 'bar'])
    >>> methodfinder.find([1,2], '__iter__', whichEvaluatesTo=True)
    hasattr([1, 2], '__iter__')
    >>> methodfinder.find(itertools, [1,2], whichEvaluatesTo=[[1,2],[2,1]])
    <module 'itertools' (built-in)>.permutations([1, 2])
    >>> methodfinder.find(itertools, [1,2], [3,4], whichEvaluatesTo=[[1,3],[2,4]])
    <module 'itertools' (built-in)>.zip_longest([1, 2], [3, 4])
    >>> methodfinder.find([], whichEvaluatesTo=0)
    len([])
    sum([])
    >>> methodfinder.find([], whichEvaluatesTo=False)
    any([])
    bool([])
    callable([])
    >>> methodfinder.find(3, whichEvaluatesTo="3")
    ascii(3)
    format(3)
    repr(3)
    str(3)
    >>> methodfinder.find(-1,3, whichEvaluatesTo=2)
    -1%3
    -1+3
    3+-1
    >>> methodfinder.find(3,2, whichEvaluatesTo=1.5)
    3/2
    >>> methodfinder.find(-1, whichEvaluatesTo=1)
    -(-1)
    -1.bit_length()
    -1.denominator
    abs(-1)
    >>> methodfinder.find(1,2, whichEvaluatesTo=3)
    1+2
    1^2
    1|2
    2+1
    2^1
    2|1
    >>> methodfinder.find(1,1, whichEvaluatesTo=1)
    1&1
    1**1
    1*1
    1.__class__(1)
    1.denominator
    1.numerator
    1.real
    1//1
    1|1
    max(1, 1)
    min(1, 1)
    pow(1, 1)
    round(1, 1)
"""

    # the main procedure.  Find any method calls on all objects, and syntax, which
    # results in the arguments evaluating to the desired result.
    # returns an iterator of strings, which when evaluated, equal the result.
    # This iterator may contain duplicates, which need to be removed
    def find():
        defaultModules = [functools, itertools]

        # get all permutations of the argument list.
        # deep copy each argument to protect against accidental mutation
        # by attribute calls
        for firstObject, *restObjects in _deep_copy_all_objects(itertools.permutations(objects)):

            # test if any of the builtin functions, when applied to the arguments
            # evaluate to the desired result.
            # not every builtin function should be called.  print and input
            # do IO, and breakpoint invokes the debugger.
            # But all other builtin fns need to be tested
            for fn in filter(lambda x: not x in ['print', 'input', 'breakpoint'],
                             dir(builtins)):
                # because the builtin procedures may take a different number
                # of arguments than provided, or the types may not match
                # the expected types, exceptions will frequently be thrown
                # rather than having large try/except blocks which just pass
                # in the body of the exception handler, use contextlib
                # to auto pass on exceptions
                with contextlib.suppress(*_errorsToIgnore):
                    # get the builtin procedure, apply it to the arguments,
                    # and test if the result is the desired result

                    argList = ([firstObject] + restObjects)
                    if _testForEqualityNestedlyAndBlockImplicitBool(getattr(builtins, fn)(*argList),
                                                                    whichEvaluatesTo):
                        yield fn + "(" + _reprArgList(argList) + ")"

            # test if any of the attributes, when applied to the arguments
            # evaluate to the desired result

            # get the name of each attribute of the first object, and the associated
            # procedure.
            for attributeName, attribute in [(d, getattr(firstObject, d)) for d in dir(firstObject)]:
                # getting the attribute doesn't always return a function as a value of the attribute
                # sometimes it returns a non function value.
                # test to see if that value is the desired result
                if _testForEqualityNestedlyAndBlockImplicitBool(attribute, whichEvaluatesTo):
                    yield repr(firstObject)+"."+attributeName
                # if the attribute is a procedure
                elif callable(attribute):
                    # test if the application of the attribute procedure to the argument list
                    # evaluates to the desired result

                    # Rather than using a large try/except block, in which the except block would
                    # just pass, use contextlib.suppress catch exceptions, and auto-pass
                    with contextlib.suppress(*_errorsToIgnore):
                        # evaulate the application the attribute procedure to the remaining arguments, test if
                        # if equals the desired result.
                        if _testForEqualityNestedlyAndBlockImplicitBool(attribute(*restObjects), whichEvaluatesTo):
                            result = _pretty_print_results(
                                whichEvaluatesTo, firstObject, restObjects, attribute, attributeName)
                            # if the returned value is not None, then we found a match!
                            if result:
                                yield result

    # remove the duplicates by putting the iterator into a set, and then
    # sort the unique results, for the purpose of deterministic outputs
    # for unit testing
    for x in sorted(set(find())):
        print(x)


def _deep_copy_all_objects(objs):
    """Deep copy all objects that are deep-copiable, without failing on objects which can't (i.e. modules)
"""
    for o in objs:
        try:
            yield copy.deepcopy(o)
        except:
            yield o


def _testForEqualityNestedlyAndBlockImplicitBool(o1, o2):
    """test objects, or sequences, for equality. sequences are tested recursively.  Block
    implicit conversion of values to bools.

    >>> import methodfinder
    >>> methodfinder._testForEqualityNestedlyAndBlockImplicitBool(1,1)
    True
    >>> methodfinder._testForEqualityNestedlyAndBlockImplicitBool(1,2)
    False
    >>> methodfinder._testForEqualityNestedlyAndBlockImplicitBool([1,2,3],[1,2,3])
    True
    >>> methodfinder._testForEqualityNestedlyAndBlockImplicitBool([1,2,3],[2,1,3])
    False
    >>> methodfinder._testForEqualityNestedlyAndBlockImplicitBool(1,True)
    False
"""
    try:
        # if they have iterators, no exception will be thrown

        # take 100 elements from them.  any user of methodfinder
        # will not be putting in more than 100 elements
        # if it's not an iterator, an exception will be thrown
        for e1, e2 in itertools.zip_longest(itertools.islice(o1, 100),
                                            itertools.islice(o2, 100)):
            if not _testForEqualityNestedlyAndBlockImplicitBool(e1, e2):
                return False
        return True
    except:
        # since at least one of the objects does not have an iterator,
        # just test for equality normally.
        # test that the types are the same to suppress implicit
        # conversion of values to bools, which returns
        # way too many useless results for the purpose of methodfinder
        return (o1 == o2) and (type(o1) == type(o2))


def _pretty_print_results(whichEvaluatesTo, firstObject, restObjects, attribute, attributeName):
    # if only a single object
    if not restObjects:
        # these procedures are already tested by the builtin
        # procedures, so no need to print them out twice,
        # nor format them specially
        toSkip = {"__abs__": "abs",
                  "__bool__": "bool",
                  "__repr__": "repr",
                  "__str__": "str",
                  "__len__": "len",
                  }
        prefixSyntax = {"__neg__": "-",
                        }
        if attributeName in prefixSyntax.keys():
            return prefixSyntax[attributeName] + "(" + repr(firstObject) + ")"
        elif attributeName not in toSkip.keys():
            return repr(firstObject)+"." + attributeName+"()"
    # if there are more than 1 argument
    else:
        if attributeName == "__contains__":
            return _reprArgList(restObjects) + " in " + repr(firstObject)
        # don't bother testing the r methods.  They have equivalent
        # procedures where the inputs are reversed, which are already
        # testing because of the call to permutations.
        toSkip = ["__rmod__",
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
        if attributeName in toSkip:
            return
        # rather than printing out the method calls
        # for double underscore methods, instead print the
        # syntax that implicitly calls these methods
        infixBuiltins = {"__add__": "+",
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

        argListToPrint = _reprArgList(restObjects)
        if attributeName in infixBuiltins.keys():
            return repr(firstObject) + infixBuiltins[attributeName] + argListToPrint
        else:
            return repr(firstObject) + "." + attributeName + "(" + argListToPrint + ")"


def _reprArgList(l):
    """pretty print a list of arguments

    >>> import methodfinder
    >>> methodfinder._reprArgList([1,2,3,'4'])
    "1, 2, 3, '4'"
"""
    return ", ".join(map(repr, l))


# the list of errors which can occur, which need to be suppressed.
# these errors can occur because we may be calling a procedure with the
# wrong number of arguments, the wrong types, etc.
_errorsToIgnore = [TypeError, ValueError, SystemExit,
                   OSError, IndexError, ModuleNotFoundError, AttributeError]
