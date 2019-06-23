methodfinder

Python tool to find a method that you know must exist.

Sometimes you know the inputs and outputs for a procedure, but you don't remember the name.
methodfinder.find tries to find the name.

```python
>>> import methodfinder
>>> for x in methodfinder.find(argList=[-1], desiredResult=1): print(x)
...
('-1', '__abs__')
('-1', '__bool__')
('-1', '__neg__')
('-1', 'bit_length')
('-1', 'denominator')
>>> for x in methodfinder.find(argList=[" ",["foo", "bar"]], desiredResult="foo bar"): print(x)
...
(' ', 'join', ["['foo', 'bar']"])
"""
```
