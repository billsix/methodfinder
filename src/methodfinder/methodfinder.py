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
    >>> methodfinder.find(" ",["foo", "bar"], whichEvaluatesTo="foo bar")
    ' '.join(['foo', 'bar'])
    >>> methodfinder.find([1,2,3], whichEvaluatesTo=6)
    sum([1, 2, 3])
    >>> methodfinder.find(itertools, [1,2], whichEvaluatesTo=[[1,2],[2,1]])
    <module 'itertools' (built-in)>.permutations([1, 2])
    >>> methodfinder.find(itertools, [1,2], [3,4], whichEvaluatesTo=[[1,3],[2,4]])
    <module 'itertools' (built-in)>.zip_longest([1, 2], [3, 4])
    >>> methodfinder.find([], whichEvaluatesTo=False)
    any([])
    bool([])
    callable([])
    len([])
    sum([])
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
    bool(-1)
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
    1/1
    1<=1
    1==1
    1>=1
    1|1
    max(1)
    min(1)
    pow(1)
    round(1)
"""
    def find():
        defaultModules = [functools, itertools]

        for firstObject, *restObjects in _deep_copy_all_objects(itertools.permutations(objects)):
            for fn in filter(lambda x: not x in ['print', 'input', 'breakpoint'],
                             dir(builtins)):
                with contextlib.suppress(*_errorsToIgnore):
                    if _testForEqualityNestedly(getattr(builtins, fn)(*([firstObject] + restObjects)),
                                               whichEvaluatesTo):
                        yield fn + "(" + repr(firstObject) + ")"
            for attributeName, attribute in [(d, getattr(firstObject, d)) for d in dir(firstObject)]:
                if attribute == whichEvaluatesTo:
                    yield str(repr(firstObject)+"."+str(attributeName))
                elif callable(attribute):
                    result = _pretty_print_results(whichEvaluatesTo, firstObject, restObjects, attribute, attributeName)
                    if result:
                        yield result

    for x in sorted(set(find())): print(x)

# so that all objects which are deep-copiable can be copied
# while not failing on objects which can't (i.e. modules)
def _deep_copy_all_objects(objs):
    for o in objs:
        try:
            yield copy.deepcopy(o)
        except:
            yield o



# test objects, or sequences, for equality
# sequences are tested recursively
def _testForEqualityNestedly(o1, o2):
    try:
        # if they have iterators, no exception will be thrown

        # take 100 elements from them.  any user of methodfinder
        # will not be putting in more than 100 elements
        # if it's not an iterator, an exception will be thrown
        for e1, e2 in itertools.zip_longest(itertools.islice(o1, 100),
                                            itertools.islice(o2, 100)):
            if not _testForEqualityNestedly(e1, e2):
                return False
        return True
    except:
        # since at least one of the objects does not have an iterator,
        # just test for equality normally
        return o1 == o2

def _pretty_print_results(whichEvaluatesTo, firstObject, restObjects, attribute, attributeName):
    with contextlib.suppress(*_errorsToIgnore):
        if _testForEqualityNestedly(attribute(*restObjects), whichEvaluatesTo):
            if not restObjects:
                toSkip = {"__abs__": "abs",
                          "__bool__": "bool",
                          "__repr__": "repr",
                          "__str__": "str",
                          "__len__": "len",
                          }
                prefixSyntax = {"__neg__": "-",
                                }
                if attributeName in prefixSyntax.keys():
                    return str(prefixSyntax[attributeName] +
                               "(" + str(firstObject) + ")")
                elif attributeName not in toSkip.keys():
                    return str(repr(firstObject)+"." +
                               str(attributeName)+"()")
            else:
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
                argListToPrint = repr([list(restObjects)])[2:-2]
                if attributeName in infixBuiltins.keys():
                    return str(repr(firstObject) +
                               infixBuiltins[attributeName] + argListToPrint)
                else:
                    return str(repr(firstObject) + "." + attributeName +
                               "(" + argListToPrint + ")")

_errorsToIgnore = [TypeError, ValueError, SystemExit, OSError, IndexError, ModuleNotFoundError, AttributeError]
