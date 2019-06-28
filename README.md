methodfinder

Python tool to find a method that you know must exist.

Sometimes you know the inputs and outputs for a procedure, but you don't remember the name.
methodfinder.find tries to find the name.

```python
>>> import methodfinder
>>> import itertools
>>> methodfinder.find(" ",["foo", "bar"], whichEvaluatesTo="foo bar")
' '.join(['foo', 'bar'])
>>> methodfinder.find(itertools, [1,2], whichEvaluatesTo=[[1,2],[2,1]])
<module 'itertools' (built-in)>.permutations([1, 2])
>>> methodfinder.find(itertools, [1,2], [3,4], whichEvaluatesTo=[[1,3],[2,4]])
<module 'itertools' (built-in)>.zip_longest([1, 2], [3, 4])
>>> methodfinder.find([], whichEvaluatesTo=False)
[].__len__()
>>> methodfinder.find(3, whichEvaluatesTo="3")
repr(3)
str(3)
>>> methodfinder.find(-1,3, whichEvaluatesTo=2)
-1+3
-1%3
3+-1
>>> methodfinder.find(3,2, whichEvaluatesTo=1.5)
3/2
2.__rtruediv__(3)
>>> methodfinder.find(-1, whichEvaluatesTo=1)
abs(-1)
bool(-1)
-(-1)
-1.bit_length()
-1.denominator
```
