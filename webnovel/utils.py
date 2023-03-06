"""General Utilities - written in support of the rest of the code."""

import io
import string
from typing import IO, Union

BASE_DIGITS = string.digits + string.ascii_letters


def merge_dicts(*dicts, nested: bool = False, use_first: bool = False, factory: type[dict] = dict) -> dict:
    """
    Merge a series of dictionaries together into a new result.

    Dictionaries are merged together in sequence. Key collisions will result in the last dictionary's value "winning"
    out (all previous values overwritten). For example::

        >>> dict_1 = {"a": 1, "b": 2}
        >>> dict_2 = {"a": 2, "c": 4}
        >>> dict_3 = {"a": 5, "e": "f"}
        >>> result = merge_dicts(dict_1, dict_2, dict_3)
        >>> assert result == {"a": 5, "b": 2, "c": 4, "e": "f"}

    ..note::
        Unless the use_first option is specified, the result is stored in a completely new dictionary. This operation
        should be completely non-destructive to all dictionaries (as long as use_first is False).

    When nested-mode is on, nested dictionaries (in the values) will be parsed down into and recursively merged together
    as well. See the example below.

    Non-nested Example::
        >>> dict_1 = {"a": 1, "b": 2}
        >>> dict_2 = {"a": 3, "c": 4}
        >>> dict_3 = merge_dicts(dict_1, dict_2)
        >>> assert id(dict_1) != id(dict_3)
        >>> assert id(dict_2) != id(dict_3)
        >>> assert dict_3 == {"a": 3, "b": 2, "c": 4}

    Nested Example::
        >>> dict_1 = {"a": {"b": {"c": 1, "d": 4}}, "g": 1}
        >>> dict_2 = {"a": {"b": {"c": 2, "e": 6}}, "g": 2}
        >>> merge_dicts(dict_1, dict_2, nested=True)
        {
            "a": {
                "b": {
                    "c": 2,
                    "d": 4,
                    "e": 6,
                }
            },
            "g": 2
        }
        >>> dict_3 = {"a": {"b": 1}}
        >>> merge_dicts(dict_1, dict_2, dict_3, nested=True)
        {
            "a": {
                "b": 1
            },
            "g": 2
        }

    :param dicts: A variable number of dictionaries to merge together.
    :param nested: (optional) A boolean controlling whether (or not) to merge in nested mode. (Defaults to False)
    :param use_first: (optional) Don't create a new dict. Merge all dicts into the first dict provided in the args. By
        default, this of turned off.
    :param factory: (optional) When creating a new dict use this factory to create the instance. Defaults to dict().
    """

    def _merge_nested_dicts(dest: dict, *dicts_to_merge):
        if not isinstance(dest, dict):
            raise ValueError(f"Destination needs to be a dict, not {type(dest)}")
        for key, value in [d.items() for d in dicts_to_merge]:
            should_merge = key in dict and isinstance(dest[key], dict) and isinstance(value, dict)
            dest[key] = (
                _merge_nested_dicts(factory(dest[key]), value)
                if should_merge
                else _merge_nested_dicts(factory(), value)
                if isinstance(value, dict)
                else value
            )
        return dest

    if use_first:
        result = dicts[0]
        dicts = dicts[1:]
    else:
        result = factory()

    for idx, current in enumerate(dicts):
        if not isinstance(current, dict):
            raise ValueError(f"{type(current)} is not a dict (arg: {idx}): {current!r}")
        if nested:
            _merge_nested_dicts(result, current)
        else:
            result.update(current)

    return result


def normalize_io(file_or_io: Union[IO, str] = None, mode: str = "rb") -> IO:
    """
    Take in a filename or IO instance and return an IO instance.

    The purpose of this
    """
    if file_or_io is None:
        return io.BytesIO()
    if isinstance(file_or_io, str):
        return open(file_or_io, mode=mode)
    return file_or_io


def int2base(x: int, base: int) -> str:
    """
    Convert an int to a string of a specific base.

    SOURCE: https://stackoverflow.com/questions/2267362/how-to-convert-an-integer-to-a-string-in-any-base

    :param x: The integer to convert.
    :param base: The base to convert to.
    """
    if x < 0:
        sign = -1
    elif x == 0:
        return BASE_DIGITS[0]
    else:
        sign = 1

    x *= sign
    digits = []

    while x:
        digits.append(BASE_DIGITS[x % base])
        x = x // base

    if sign < 0:
        digits.append("-")

    digits.reverse()

    return "".join(digits)
