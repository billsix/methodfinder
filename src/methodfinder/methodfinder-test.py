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

import methodfinder
import itertools
import doctest
import unittest

class TestMethodFinder(unittest.TestCase):

    def test_in(self):
        self.assertListEqual(methodfinder._find([[1,2,6,7], 6], which_evaluates_to=True),
                             ["6 in [1, 2, 6, 7]\n[1, 2, 6, 7].__contains__(6)"])

    def test_join(self):
        self.assertListEqual(methodfinder._find([" ",["foo", "bar"]], which_evaluates_to="foo bar"),
                             ["' '.join(['foo', 'bar'])"])

    def test_permutations(self):
        self.assertListEqual(methodfinder._find([itertools, [1,2]], which_evaluates_to=[[1,2],[2,1]]),
                             ["itertools.permutations([1, 2])"])

    def test_zip(self):
        self.assertListEqual(methodfinder._find([[1,2], [3,4]], which_evaluates_to=[[1,3],[2,4]]),
                             ["zip([1, 2], [3, 4])"])

    def test_zip(self):
        self.assertListEqual(methodfinder._find([itertools, [1,2], [3,4]], which_evaluates_to=[[1,3],[2,4]]),
                             ["itertools.zip_longest([1, 2], [3, 4])"])

    def test_len(self):
        self.assertListEqual(methodfinder._find([[]], which_evaluates_to=0),
                             ["len([])",
                             "sum([])"])

    def test_any(self):
        self.assertListEqual(methodfinder._find([[]], which_evaluates_to=False),
                             ["any([])",
                              "bool([])",
                              "callable([])"])

    def test_str(self):
        self.assertListEqual(methodfinder._find([3], which_evaluates_to="3"),
                             ["ascii(3)",
                              "format(3)",
                              "repr(3)",
                              "str(3)"])

    def test_add(self):
        self.assertListEqual(methodfinder._find([-1,3], which_evaluates_to=2),
                             ["-1%3",
                              "-1+3",
                              "3+-1"])

    def test_divide(self):
        self.assertListEqual(methodfinder._find([3,2], which_evaluates_to=1.5),
                             ["3/2"])

    def test_doublenegative(self):
        self.assertListEqual(methodfinder._find([-1], which_evaluates_to=1),
                             ["-(-1)",
                              "-1.bit_length()",
                              "-1.denominator",
                              "abs(-1)"])

    def test_add2(self):
        self.assertListEqual(methodfinder._find([1,2], which_evaluates_to=3),
                             ["1+2",
                              "1^2",
                              "1|2",
                              "2+1",
                              "2^1",
                              "2|1"])

    def test_one_one_one(self):
        self.assertListEqual(methodfinder._find([1,1], which_evaluates_to=1),
                             ["1&1",
                              "1**1",
                              "1*1",
                              "1.__class__(1)",
                              "1.denominator",
                              "1.numerator",
                              "1.real",
                              "1//1",
                              "1|1",
                              "max(1, 1)",
                              "min(1, 1)",
                              "pow(1, 1)",
                              "round(1, 1)"])

    def test_hasattr(self):
        self.assertListEqual(methodfinder._find([[1,2], '__iter__'], which_evaluates_to=True),
                             ["hasattr([1, 2], '__iter__')"])

    def test_doctest(self):
        failureCount, testCount = doctest.testmod(methodfinder)
        self.assertEqual(0, failureCount)


if __name__ == "__main__":
    unittest.main()
