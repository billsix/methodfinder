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
    -1+3
    -1%3
    3+-1
    >>> methodfinder.find(3,2, whichEvaluatesTo=1.5)
    3/2
    >>> methodfinder.find(-1, whichEvaluatesTo=1)
    abs(-1)
    bool(-1)
    -(-1)
    -1.bit_length()
    -1.denominator
"""
    # so that all objects which are deep-copiable can be copied
    # while not failing on objects which can't (i.e. modules)
    def deep_copy_all_objects(objs):
        for o in objs:
            try:
                yield copy.deepcopy(o)
            except:
                yield o

    # get built in functions, but remove ones which will print things
    # out unnecessarily
    builtInFns = filter(lambda x: not x in ['print', 'input', 'breakpoint'],
                        dir(builtins))

    # test objects, or sequences, for equality
    # sequences are tested recursively
    def testForEqualityNestedly(o1, o2):
        try:
            # if they have iterators, no exception will be thrown

            # take 100 elements from them.  any user of methodfinder
            # will not be putting in more than 100 elements
            # if it's not an iterator, an exception will be thrown
            for e1, e2 in itertools.zip_longest(itertools.islice(o1, 100),
                                                itertools.islice(o2, 100)):
                if not testForEqualityNestedly(e1, e2):
                    return False
            return True
        except:
            # since at least one of the objects does not have an iterator,
            # just test for equality normally
            return o1 == o2



    for firstObject, *restObjects in deep_copy_all_objects(itertools.permutations(objects)):
        for fn in builtInFns:
            #print("trying")
            #print(fn)
            try:
                if testForEqualityNestedly(getattr(builtins, fn)(*([firstObject] + restObjects)),
                                           whichEvaluatesTo):
                    print(fn + "(" + repr(firstObject) + ")")
            except:
                pass
        for attributeName, attribute in [(d, getattr(firstObject, d)) for d in dir(firstObject)]:
            if attribute == whichEvaluatesTo:
                print(repr(firstObject)+"."+str(attributeName))
            elif callable(attribute):
                try:
                    # try all of the permutations of methods.  If a method call
                    # fails, an exception will be thrown and ignored below.
                    # if the method's result equals the desired result, print
                    # out the expression

                    if testForEqualityNestedly(attribute(*restObjects), whichEvaluatesTo):
                        if not restObjects:
                            toSkip = {"__abs__": "abs",
                                      "__bool__": "bool",
                                      "__repr__": "repr",
                                      "__str__": "str",
                                      "__len__": "len"
                            }
                            prefixSyntax = {"__neg__": "-",
                            }
                            if attributeName in prefixSyntax.keys():
                                print(prefixSyntax[attributeName] +
                                      "(" + str(firstObject) + ")")
                            elif attributeName not in toSkip.keys():
                                print(repr(firstObject)+"." +
                                      str(attributeName)+"()")
                        else:
                            toSkip = ["__rmod__",
                                      "__radd__",
                                      "__rtruediv__"
                                      ]
                            if attributeName in toSkip:
                                continue
                            infixBuiltins = {"__add__": "+",
                                             "__mod__": "%",
                                             "__sub__": '-',
                                             "__mul__": '*',
                                             "__truediv__": '/'}
                            argListToPrint = repr([list(restObjects)])[2:-2]
                            if attributeName in infixBuiltins.keys():
                                print(repr(firstObject) +
                                      infixBuiltins[attributeName] + argListToPrint)
                            else:
                                print(repr(firstObject) + "." + attributeName +
                                      "(" + argListToPrint + ")")
                except:
                    # the method call failed, so the result is not the desired result,
                    # so do nothing
                    pass
