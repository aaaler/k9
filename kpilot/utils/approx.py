"""This module exposes the Approx class which allows approximate comparison of floating point
values. Two values are considered equal if their relative difference is smaller than a given
relative tolerance (http://en.wikipedia.org/wiki/Relative_difference). The base comparison is:

    |x-y| / max(|x|,|y|) < rtol

This formula breaks down when one of the numbers is 0, since no number other than 0 itself is
considered approximately == 0 unless rtol is > 1. Replacing x by 0 in the formula and assuming
y != 0, yields

    |y| / |y| < rtol

So rtol would effectively need to be > 1 for the formula to accept any non-zero number as "close
enough" to 0. Note however that rtol should normally be a small positive number (e.g. 1e-6), so
this is not satisfactory.

To fix this, we introduce a second tolerance parameter: absolute tolerance. First, we transform the
previous inequation by multiplying both sides by max(|x|,|y|). Since this is > 0 (because at least
one of the numbers is != 0), the direction of the inequation is maintained, leading to

    |x-y| < rtol * max(|x|,|y|)

Now, we simply add the absolute tolerance to the right-hand side of the inequation

    |x-y| < atol + rtol * max(|x|,|y|)

This keeps at least the absolute tolerance for when one of the numbers is 0. Additionally, the
influence of absolute tolerance should fade when comparing large numbers, since the rtol component
should be much larger.
"""
from itertools import izip_longest
from collections import Iterable
from contextlib import contextmanager
from numbers import Real

from utils.misc import check_type, NAN


_rtol = 1e-9   # default relative tolerance
_atol = 1e-12  # default absolute tolerance


# ------------------------------------------------------------------------------
# Relative tolerance functions
def get_rtol():
    global _rtol
    return _rtol


def set_rtol(rtol):
    global _rtol
    check_type(rtol, Real)
    if rtol < 0.0:
        raise ValueError("relative tolerance must be non-negative")
    _rtol = rtol


@contextmanager
def temp_rtol(rtol):
    global _rtol
    prev_rtol = _rtol
    set_rtol(rtol)
    yield
    set_rtol(prev_rtol)


# ------------------------------------------------------------------------------
# Absolute tolerance functions
def get_atol():
    global _atol
    return _atol


def set_atol(atol):
    global _atol
    check_type(atol, Real)
    if atol < 0.0:
        raise ValueError("absolute tolerance must be non-negative")
    _atol = atol


@contextmanager
def temp_atol(atol):
    global _atol
    prev_atol = _atol
    set_atol(atol)
    yield
    set_atol(prev_atol)


# ------------------------------------------------------------------------------
# Final tolerance computation and rich comparison functions
def tolerance(x, y):
    """Compute the tolerance for the approximate comparison of x and y."""
    global _atol, _rtol
    x = float(x)
    y = float(y)
    return _atol + _rtol * max(abs(x), abs(y))


def _op(x, y, operator):
    x_is_iterable = isinstance(x, Iterable)
    y_is_iterable = isinstance(y, Iterable)
    if x_is_iterable and y_is_iterable:
        return all(_op(u, v, operator) for u, v in izip_longest(x, y, fillvalue=NAN))
    elif x_is_iterable:
        return all(_op(u, y, operator) for u in x)
    elif y_is_iterable:
        return all(_op(x, v, operator) for v in y)
    else:
        return operator(Approx(x), y)


def eq(x, y):
    return _op(x, y, Approx.__eq__)


def ne(x, y):
    return _op(x, y, Approx.__ne__)


def le(x, y):
    return _op(x, y, Approx.__le__)


def lt(x, y):
    return _op(x, y, Approx.__lt__)


def ge(x, y):
    return _op(x, y, Approx.__ge__)


def gt(x, y):
    return _op(x, y, Approx.__gt__)


class Approx(float):
    """A float subclass to deal with floating point rounding errors by comparing approximately.
    Comparison operators are redefined to use absolute and relative tolerance.
    """
    __slots__ = ()  # prevent creation of a dictionary per Approx instance

    def __repr__(self):
        return float.__repr__(self) + "~"

    def __str__(self):
        return float.__str__(self) + "~"

    def tolerance(self, x):
        """Compute the tolerance for the approximate comparison of this number with another one."""
        global _atol, _rtol
        x = float(x)
        y = float(self)
        return _atol + _rtol * max(abs(x), abs(y))

    # --------------------------------------------------------------------------
    # Rich comparison operators
    def __eq__(self, x):
        """Approximate floating point comparison using absolute and relative epsilons. For two
        numbers x and y, this method is equivalent to:
            def almost_equal(x, y):
                return (x == y) or (abs(x - y) <= atol + rtol * max(abs(x), abs(y)))

        This is very similar to what is done in numpy, but this is symmetric, that is, the order
        of the two numbers is irrelevant to the result. In numpy.isclose(), the relative tolerance
        is multiplied by the absolute value of the second number, so calling the function with
        reversed arguments can give different results, which makes no sense at all. They're even
        aware of that, there's a note on their website, but they don't fix it for some reason..."""
        global _atol, _rtol
        x = float(x)
        y = float(self)
        if x == y:
            return True
        z = abs(x - y) - _atol
        return z <= 0.0 or z <= _rtol * max(abs(x), abs(y))

    def __ne__(self, x):
        return not self.__eq__(x)

    def __le__(self, x):
        return float(self) <= x or self.__eq__(x)

    def __lt__(self, x):
        return float(self) < x and not self.__eq__(x)

    def __ge__(self, x):
        return float(self) >= x or self.__eq__(x)

    def __gt__(self, x):
        return float(self) > x and not self.__eq__(x)

    # --------------------------------------------------------------------------
    # Arithmetic operators
    def __neg__(self):
        return type(self)(-float(self))

    def __pos__(self):
        return type(self)(self)

    def __abs__(self):
        return type(self)(abs(float(self)))

    def __add__(self, other):
        return type(self)(float(self) + other)

    def __sub__(self, other):
        return type(self)(float(self) - other)

    def __mul__(self, other):
        return type(self)(float(self) * other)

    def __div__(self, other):
        return type(self)(float(self) / other)

    __truediv__ = __div__

    def __floordiv__(self, other):
        return type(self)(float(self) // other)

    def __mod__(self, other):
        return type(self)(float(self) % other)

    def __divmod__(self, other):
        return type(self)(divmod(float(self), other))

    def __pow__(self, other, modulo=None):
        return type(self)(pow(float(self), other, modulo))

    __radd__ = __add__

    def __rsub__(self, other):
        return type(self)(other - float(self))

    __rmul__ = __mul__

    def __rdiv__(self, other):
        return type(self)(other / float(self))

    __rtruediv__ = __rdiv__

    def __rfloordiv__(self, other):
        return type(self)(other // float(self))

    def __rmod__(self, other):
        return type(self)(other % float(self))

    def __rdivmod__(self, other):
        return type(self)(divmod(other, float(self)))

    def __rpow__(self, other):
        return type(self)(other ** float(self))

