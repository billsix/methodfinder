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
    for firstObject, *restObjects in map(copy.deepcopy, itertools.permutations(objects)):
        for d in dir(firstObject):
            attribute = getattr(firstObject, d)
            if attribute == whichEvaluatesTo:
                print(repr(firstObject)+"."+repr(d))
            elif callable(attribute):
                try:
                    if attribute(*restObjects) == whichEvaluatesTo:
                        if not restObjects:
                            prefixBuiltins = {"__abs__": "abs",
                                              "__bool__": "bool",
                                              "__neg__": "-",
                                              "__repr__": "repr"}
                            if d in prefixBuiltins.keys():
                                print(prefixBuiltins[d]+"("+repr(firstObject)+")")
                            else:
                                print(repr(firstObject)+"."+repr(d)+"()")
                        else:
                            infixBuiltins = {"__add__": "+",
                                             "__mod__": "%",
                                             "__sub__": '-',
                                             "__mul__": '*',
                                             "__truediv__": '/'}
                            argListToPrint = repr(list(restObjects))
                            if d in infixBuiltins.keys():
                                print(repr(firstObject) + infixBuiltins[d] + argListToPrint[2:-2])
                            else:
                                argListToPrint = repr(list(restObjects))
                                print(repr(firstObject)+ "." + d + "(" + argListToPrint[2:-2] + ")")
                except:
                    pass
