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


def testForEquality(o1, o2):
    try:
        # take 100 elements from them.  any user of methodfinder
        # will not be putting in more than 100 elements
        # if it's not an iterator, an exception will be thrown
        for e1, e2 in list(itertools.zip_longest(list(itertools.islice(o1, 100)),
                                                 list(itertools.islice(o2, 100)))):
            if not testForEquality(e1, e2):
                return False
        return True
    except:
        return o1 == o2


def find(*objects, whichEvaluatesTo):
    """Sometimes you know the inputs and outputs for a procedure, but you don't remember the name.
    methodfinder.find tries to find the name.

    >>> import methodfinder
    >>> methodfinder.find(-1, whichEvaluatesTo=1)
    abs(-1)
    bool(-1)
    -(-1)
    -1.bit_length
    -1.denominator
    >>> methodfinder.find(" ",["foo", "bar"], whichEvaluatesTo="foo bar")
    " ".join(['foo', 'bar'])
"""
    # so that all objects which are deep-copiable can be copied
    # while not failing on objects which can't (i.e. modules)
    def deep_copy_all_objects(objs):
        for o in objs:
            try:
                yield copy.deepcopy(o)
            except:
                yield o

    for firstObject, *restObjects in deep_copy_all_objects(itertools.permutations(objects)):
        for d in dir(firstObject):
            attribute = getattr(firstObject, d)
            if attribute == whichEvaluatesTo:
                print(repr(firstObject)+"."+str(d))
            elif callable(attribute):
                try:
                    if testForEquality(attribute(*restObjects), whichEvaluatesTo):
                        if not restObjects:
                            prefixBuiltins = {"__abs__": "abs",
                                              "__bool__": "bool",
                                              "__neg__": "-",
                                              "__repr__": "repr",
                                              "__str__": "str",
                                              "__len__": "len"
                                              }
                            if d in prefixBuiltins.keys():
                                print(prefixBuiltins[d] +
                                      "("+str(firstObject)+")")
                            else:
                                print(repr(firstObject)+"."+str(d)+"()")
                        else:
                            toSkip = ["__rmod__",
                                      "__radd__",
                                      "__rtruediv__"
                                      ]
                            if d in toSkip:
                                continue
                            infixBuiltins = {"__add__": "+",
                                             "__mod__": "%",
                                             "__sub__": '-',
                                             "__mul__": '*',
                                             "__truediv__": '/'}
                            argListToPrint = repr([list(restObjects)])
                            if d in infixBuiltins.keys():
                                print(repr(firstObject) +
                                      infixBuiltins[d] + argListToPrint[2:-2])
                            else:
                                print(repr(firstObject) + "." + d +
                                      "(" + argListToPrint[2:-2] + ")")
                except:
                    pass
