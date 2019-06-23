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

def find(argList, desiredResult):
    """Sometimes you know the inputs and outputs for a procedure, but you don't remember the name.
    methodfinder.find tries to find the name.

    >>> import methodfinder
    >>> methodfinder.find(argList=[-1], desiredResult=1)
    ('-1', '__abs__')
    ('-1', '__bool__')
    ('-1', '__neg__')
    ('-1', 'bit_length')
    ('-1', 'denominator')
    >>> methodfinder.find(argList=[" ",["foo", "bar"]], desiredResult="foo bar")
    (' ', 'join', ["['foo', 'bar']"])
"""
    objectPermutations = itertools.permutations(argList)
    for p in objectPermutations:
        firstArg = p[0]
        rest = p[1:]

        dirs = dir(firstArg)
        for d in dirs:
            attribute = getattr(firstArg, d)
            if attribute == desiredResult:
                print((str(firstArg), d))
            if callable(attribute):
                try:
                    if attribute(*rest) == desiredResult:
                        if len(rest) == 0:
                            print((str(firstArg), d))
                        else:
                            print((str(firstArg), d, list(map(str, rest))))
                except:
                    pass
