methodfinder

Python tool to find a method that you know must exist.

Sometimes you know the inputs and outputs for a procedure, but you don't remember the name.
methodfinder.find tries to find the name.

```python
>>> import methodfinder
>>> methodfinder.find(" ",["foo", "bar"], whichEvaluatesTo="foo bar")
" ".join(['foo', 'bar'])
>>>
>>> methodfinder.find([], whichEvaluatesTo=False)
[].__len__()
>>>
>>> methodfinder.find(3, whichEvaluatesTo="3")
3.__repr__
str(3)
>>>
>>> methodfinder.find(-1,3, whichEvaluatesTo=2)
-1+3
-1%3
-1.__radd__(3)
3+-1
3.__radd__(-1)
3.__rmod__(-1)
>>>
>>> methodfinder.find(3,2, whichEvaluatesTo=1.5)
3/2
2.__rtruediv__(3)
>>>
>>> methodfinder.find(-1, whichEvaluatesTo=1)
abs(-1)
bool(-1)
-(-1)
-1.bit_length()
-1.denominator
```
