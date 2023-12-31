"""General Utilities - written in support of the rest of the code."""

from dataclasses import MISSING, Field, fields, is_dataclass
import datetime
import decimal
import enum
import inspect
import io
import itertools
import json
from pathlib import Path
import re
import string
from time import perf_counter
import types
from typing import IO, Any, Callable, ClassVar, Container, Iterator, Sequence, TypeVar, Union, get_args, get_origin

from apptk.coerce import to_datetime

BASE_DIGITS = string.digits + string.ascii_letters

T = TypeVar("T")


def clean_filename(filename: str, replace_chars: Sequence[str] = "/?:@#!$%^", sub_char: str = "_"):
    """Replace characters that might screw up the filename."""
    return re.sub(r"[" + replace_chars + "]+", sub_char, filename)


def filter_dict(_dict: dict, keys: Container) -> dict:
    """Filter a dictionary down to only the provided keys."""
    return {key: value for key, value in _dict.items() if key in keys}


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
        for key, value in itertools.chain.from_iterable(d.items() for d in dicts_to_merge):
            should_merge = key in dest and isinstance(dest[key], dict) and isinstance(value, dict)
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
    if isinstance(file_or_io, Path):
        return file_or_io.open(mode=mode)
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


def batcher_iter(seq: Sequence, batch_size: int = 100) -> Iterator[list]:
    """
    Return a generator that follows a sequence returning batches of items from the sequence.

    :param seq: A sequence to return batches from.
    :param batch_size: (optional) The size that each batch should be. Defaults
        to 100. The final batch will be less than than the batch_size unless the
        length of the sequence is a multiple of batch_size.
    """
    batch = []
    for item in seq:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if len(batch) < 1:
        return
    yield batch


class Timer:
    """
    A context-manager that records the time that the with block took to run.

    Also stores the start time and stop time timestamps.
    """

    started_at: datetime.datetime
    ended_at: datetime.datetime
    counter_start: float
    counter_end: float
    time: float | None = None

    def __enter__(self):
        """Start the timer."""
        self.started_at = datetime.datetime.utcnow()
        self.counter_start = perf_counter()
        self.time = None
        return self

    def __exit__(self, type, value, traceback):
        """Stop the timer."""
        self.ended_at = datetime.datetime.utcnow()
        self.counter_end = perf_counter()
        self.time = self.counter_end - self.counter_start


class Namespace(dict):
    """A simple wrapper around dict that allows accessing items as attributes."""

    def __getattr__(self, name):
        """Return items via __getitem__ if it's not a pre-existing attribute on self."""
        if name in self:
            return self[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute {name!r}")

    def __setattr__(self, name, value):
        """Allow setting of attributes to be handled via __setitem__."""
        self[name] = value


class DataclassSerializationMixin:
    """A Mixin to add to_dict/from_dict to dataclasses."""

    #: When initializing from a dictionary, ignore any fields that don't
    #: correspond with fields on the dataclass. If this is set to false, then the
    #: conversion will raise an exception.
    ignore_unknown_fields: ClassVar[bool] = True

    #: A list of fields that are required during conversion from a dictionary. If
    #: any of these fields are not present in the dictionary, conversion will
    #: fail with an exception.
    required_fields: ClassVar[list[str] | None] = None

    #: A mapping of type to a callable that takes a single value an returns a
    #: value. This allows specific classes/types to be mapped to a function that
    #: converts it into what this dataclass needs it to be.
    import_type_map: ClassVar[dict[type, Callable[[Any], Any]]] = {}

    #: Some common types need special handling, and it's a mess to required the
    #: user to add overrides everytime. Use import_type_map to override this.
    default_type_map: ClassVar[dict[type, Callable[[Any], Any]]] = {
        datetime.date: lambda value: to_datetime(value).date(),
        datetime.datetime: to_datetime,
    }

    @classmethod
    def get_required_fields(cls: type[T]) -> set[str]:
        """Return a set of the field names that are required to convert a dict into an instance."""
        required_fields = set()
        has_required_fields = False

        for field in fields(cls):
            field_has_no_default = field.default is MISSING and field.default_factory is MISSING
            has_required_fields = bool(cls.required_fields)

            if field_has_no_default or (has_required_fields and field.name in cls.required_fields):
                required_fields.add(field.name)

        # Check if any of the required fields in "required_fields" are not
        # returned by fields(), if there are any, then we need to raise an error
        # here.
        if has_required_fields:
            bad_fields = set(cls.required_fields) - required_fields
            if bad_fields:
                raise ValueError(f"Fields in required_fields that aren't in fields(): {tuple(bad_fields)!r}")

        return required_fields

    @classmethod
    def from_dict(cls: type[T], data: dict) -> T:
        """
        Intialize an instance from a dictionary.

        :params data: dictionary of data to parse.
        """
        field_types_map = {field.name: field.type for field in fields(cls)}
        valid_fields = set(field_types_map.keys())
        input_fields = set(data.keys())
        unknown_fields = input_fields - valid_fields

        if unknown_fields and not cls.ignore_unknown_fields:
            fields_str = ", ".join(map(repr, unknown_fields))
            raise ValueError(
                f"Cannot convert dict to {cls.__name__}: Following unknown fields encountered: {fields_str}"
            )

        if required_fields := cls.get_required_fields():
            missing_required_fields = set(required_fields) - input_fields
            if missing_required_fields:
                fields_str = ", ".join(map(repr, missing_required_fields))
                raise ValueError(f"Cannot convert dict to {cls.__name__}: Missing required fields: {fields_str}")

        kwargs = {
            key: cls._parse_field_value(value, field_type)
            for key, value in data.items()
            if (field_type := field_types_map.get(key))
        }
        return cls(**kwargs)

    @classmethod
    def _parse_field_value(cls, value, field_type: type[T]) -> T:
        """
        Convert a field value into a field_type.

        :params value: The value to convert.
        :params field_type: The type of the field.
        """
        # If the type is something like list[int], then treat `value` as a list,
        # and the items in it as `int`.
        #
        # Note: This only works for single-typed containers. If Union/UnionType
        #       are used to support multiple types, then which type to use
        #       cannot be inferred.
        if isinstance(field_type, types.GenericAlias):
            container_type = get_origin(field_type)
            items_type = get_args(field_type)[0]
            assert get_origin(items_type) is not Union, "Cannot handle typing.Union currently."
            assert type(items_type) is not types.UnionType, "Cannot handle types.UnionType currently."
            if issubclass(container_type, (Sequence, set)):
                assert isinstance(value, (Sequence, set)), "Need a sequence or a set"  # TODO better error-handling
                generator = (cls._parse_field_value(val, items_type) for val in value)
                return container_type(generator)

        # If there are any overrides to import handling, deal with them here.
        if field_type in cls.import_type_map:
            return cls.import_type_map[field_type](value)

        # if the target class is a subclass of this mixin, then use from_dict.
        # This allows for nesting of dataclasses.
        if inspect.isclass(field_type) and issubclass(field_type, DataclassSerializationMixin):
            return field_type.from_dict(value)

        # Builtin handling of common use-cases.
        if field_type in cls.default_type_map:
            return cls.default_type_map[field_type](value)

        # This should handle a bunch of common use-cases, like converting a
        # string into a number class.
        return field_type(value) if inspect.isclass(field_type) else value

    @classmethod
    def _export_field_value(cls, value, field: Field | Namespace) -> Any:
        """
        Serialize the field value.

        Based on the type of `value`, convert it into an easy to JSON-ify
        format. For example, convert dates or datetimes into ISO format.

        :params value: The value to serialize
        :params field: The dataclasses.Field to export.  Namespace type is
            allowed for recusive calls then decoding nested types.
        """
        export_mapping = {
            DataclassSerializationMixin: lambda value: value.to_dict(),
            (datetime.datetime, datetime.date): lambda value: value.isoformat(),
            enum.Enum: lambda value: value.value,
            decimal.Decimal: str,
            (Sequence, set): lambda value: value,
            Path: lambda value: str(value),
        }

        if field:
            origin_type = get_origin(field.type)
            if origin_type and issubclass(origin_type, (Sequence, set)):
                items_type = get_args(field.type)[0]
                assert type(items_type) is not types.UnionType, "Cannot handle types.UnionType currently."
                assert origin_type is not Union, "Cannot handle typing.Union currently."
                return origin_type(map(lambda v: cls._export_field_value(v, Namespace(type=items_type)), value))

        for type_, callable in export_mapping.items():
            if isinstance(value, type_):
                return callable(value)

        return value

    def to_dict(self) -> dict:
        """
        Convert dataclass instance to a dictionary.

        ..note::
            This allows more flexibility than dataclasses.asdict which parses
            through all values and uses copy.deepcopy(). This also allows for
            some flexibility in converting certain datatypes into json-ified
            types. For example, converting a datetime instance into a string.
        """
        return {field.name: self._export_field_value(getattr(self, field.name), field) for field in fields(self)}

    def to_json(self, **kwargs) -> str:
        """Convert dataclass instance to a JSON string."""
        return json.dumps(self.to_dict(), **kwargs)

    @classmethod
    def from_json(cls: type[T], data: str) -> T:
        """
        Load dataclass instance from a JSON string.

        :param data: The JSON string to parse.
        """
        return cls.from_dict(json.loads(data))
