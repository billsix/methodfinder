methodfinder

Python tool to find a method that you know must exist.

Sometimes you know the inputs and outputs for a procedure, but you don't remember the name.
methodfinder.find tries to find the name.

```python
>>> import methodfinder
>>> import itertools
>>> methodfinder.find([1,2,3]) == 6
sum([1, 2, 3])
True
>>> methodfinder.find([1,2,3]) == 7
False
>>> methodfinder.find([1,2,6,7], 6) == True
6 in [1, 2, 6, 7]
[1, 2, 6, 7].__contains__(6)
True
>>> methodfinder.find(" ",["foo", "bar"]) == "foo bar"
' '.join(['foo', 'bar'])
True
>>> methodfinder.find(itertools, [1,2]) == [[1,2],[2,1]]
itertools.permutations([1, 2])
True
>>> methodfinder.find(itertools, [1,2], [3,4]) == [[1,3],[2,4]]
itertools.zip_longest([1, 2], [3, 4])
True
>>> methodfinder.find([]) == 0
len([])
sum([])
True
>>> methodfinder.find([]) == False
any([])
bool([])
callable([])
True
>>> methodfinder.find(3) == "3"
ascii(3)
format(3)
repr(3)
str(3)
True
>>> methodfinder.find(-1,3) == 2
-1%3
-1+3
3+-1
True
>>> methodfinder.find(3,2) == 1.5
3/2
True
>>> methodfinder.find(-1) == 1
-(-1)
-1.bit_length()
-1.denominator
abs(-1)
True
>>> methodfinder.find(1,2) == 3
1+2
1^2
1|2
2+1
2^1
2|1
True
>>> methodfinder.find(1,1) == 1
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
True
>>> methodfinder.find([1,2], '__iter__') == True
hasattr([1, 2], '__iter__')
```
