from collections import defaultdict
from dataclasses import dataclass
import datetime
from io import BytesIO, TextIOWrapper
from unittest import TestCase, mock

from freezegun import freeze_time

from webnovel import utils


class CleanFilenameTestCase(TestCase):
    def test_default_replace_chars(self):
        for filename in (
            "test!file",
            "test/file",
            "test:file",
            "test?file",
            "test@file",
            "test#file",
            "test$file",
            "test%file",
            "test^file",
        ):
            with self.subTest(filename=filename):
                self.assertEqual(utils.clean_filename(filename), "test_file")

    def test_override_sub_char(self):
        for filename in (
            "test!file",
            "test/file",
            "test:file",
            "test?file",
            "test@file",
            "test#file",
            "test$file",
            "test%file",
            "test^file",
        ):
            with self.subTest(filename=filename):
                self.assertEqual(utils.clean_filename(filename, sub_char="-"), "test-file")

    def test_override_replace_chars(self):
        for filename in (
            "test!file",
            "test/file",
            "test:file",
            "test?file",
            "test@file",
            "test#file",
            "test$file",
            "test%file",
            "test^file",
        ):
            with self.subTest(filename=filename):
                self.assertEqual(utils.clean_filename(filename, replace_chars="456"), filename)

        for filename in (
            "test4file",
            "test5file",
            "test6file",
        ):
            with self.subTest(filename=filename):
                self.assertEqual(utils.clean_filename(filename, replace_chars="456"), "test_file")

    def test_handles_multiples(self):
        for filename in (
            "test!!!file",
            "test///file",
            "test:::file",
        ):
            with self.subTest(filename=filename):
                self.assertEqual(utils.clean_filename(filename), "test_file")


class FilterDictTestCase(TestCase):
    def test_creates_new_dict(self):
        expected = {"a": 1, "b": 2}
        actual = utils.filter_dict(expected, ("a", "b"))
        self.assertEqual(actual, expected)
        self.assertIsNot(actual, expected)

    def test_filters_keys(self):
        actual = utils.filter_dict({"a": 1, "b": 2, "c": 3}, ("a", "c"))
        expected = {"a": 1, "c": 3}
        self.assertEqual(actual, expected)

    def test_handles_keys_in_filter_not_in_dict(self):
        start_dict = {"a": 1, "b": 2, "c": 3}
        keys = {"a", "c", "d"}
        actual = utils.filter_dict({"a": 1, "b": 2, "c": 3}, keys)
        expected = {"a": 1, "c": 3}
        self.assertEqual(keys - set(start_dict.keys()), {"d"})
        self.assertEqual(actual, expected)


class IntegerToBaseTestCase(TestCase):
    def test_handles_base2(self):
        self.assertEqual(utils.int2base(7, 2), "111")
        self.assertEqual(utils.int2base(6, 2), "110")
        self.assertEqual(utils.int2base(10, 2), "1010")

    def test_handles_base8(self):
        self.assertEqual(utils.int2base(7, 8), "7")
        self.assertEqual(utils.int2base(16, 8), "20")
        self.assertEqual(utils.int2base(32, 8), "40")

    def test_handles_base16(self):
        self.assertEqual(utils.int2base(7, 16), "7")
        self.assertEqual(utils.int2base(16, 16), "10")
        self.assertEqual(utils.int2base(32, 16), "20")

    def test_handles_negatives(self):
        self.assertEqual(utils.int2base(-7, 16), "-7")
        self.assertEqual(utils.int2base(-16, 16), "-10")
        self.assertEqual(utils.int2base(-32, 16), "-20")

    def test_handles_zero(self):
        self.assertEqual(utils.int2base(0, 2), "0")
        self.assertEqual(utils.int2base(0, 8), "0")
        self.assertEqual(utils.int2base(0, 16), "0")
        self.assertEqual(utils.int2base(0, 32), "0")


class NormalizeIOTestCase(TestCase):
    def test_returns_bytesio_for_none(self):
        result = utils.normalize_io(None)
        self.assertIsInstance(result, BytesIO)

    def test_pass_file_like_object_just_returns_instance(self):
        with open("/tmp/.tmp", "w") as fh:
            result = utils.normalize_io(fh)
            self.assertIs(result, fh)

    def test_handles_path_to_file(self):
        result = utils.normalize_io("/tmp/.tmp", mode="w")
        self.assertIsInstance(result, TextIOWrapper)
        self.assertEqual(result.name, "/tmp/.tmp")


class MergeDictsTestCase(TestCase):
    def test_simple_dicts(self):
        d1 = {"a": 1}
        d2 = {"b": 2}
        actual = utils.merge_dicts(d1, d2)
        expected = {"a": 1, "b": 2}
        self.assertEqual(actual, expected)
        self.assertIsNot(actual, d1)
        self.assertIsNot(actual, d2)

    def test_nested_dicts_with_nested_false(self):
        d1 = {"a": {"b": 11, "c": 12}}
        d2 = {"a": {"b": 22, "d": 33}}
        expected = {"a": {"b": 22, "d": 33}}
        actual = utils.merge_dicts(d1, d2, nested=False)
        self.assertEqual(actual, expected)
        self.assertIsNot(actual, d1)
        self.assertIsNot(actual, d2)

    def test_nested_dicts_with_nested_true(self):
        d1 = {"a": {"b": 11, "c": 12}}
        d2 = {"a": {"b": 22, "d": 33}}
        expected = {"a": {"b": 22, "c": 12, "d": 33}}
        actual = utils.merge_dicts(d1, d2, nested=True)
        self.assertEqual(actual, expected)
        self.assertIsNot(actual, d1)
        self.assertIsNot(actual, d2)

    def test_use_first_does_not_create_new_dict(self):
        d1 = {"a": {"b": 11, "c": 12}}
        d2 = {"a": {"b": 22, "d": 33}}
        expected = {"a": {"b": 22, "c": 12, "d": 33}}
        actual = utils.merge_dicts(d1, d2, nested=True, use_first=True)
        self.assertEqual(actual, expected)
        self.assertEqual(d1, actual)
        self.assertIs(actual, d1)
        self.assertIsNot(actual, d2)

    def test_handles_non_dict_value(self):
        with self.assertRaises(ValueError):
            utils.merge_dicts({"a": 1}, [1, 2])

    def test_handles_non_dict_factory(self):
        with self.assertRaises(ValueError):
            utils.merge_dicts({"a": 1}, {"b": 1}, nested=True, factory=list)

    def test_factory_works(self):
        result = utils.merge_dicts({"a": 1}, {"b": 1}, factory=lambda: defaultdict(list))
        self.assertEqual(result, {"a": 1, "b": 1})
        self.assertIsInstance(result, defaultdict)


class TimerTestCase(TestCase):
    def test_start_and_stop_timestamps(self):
        with freeze_time("2012-01-14 05:47:04"):
            with utils.Timer() as timer:
                pass
        self.assertEqual(timer.started_at, datetime.datetime(2012, 1, 14, 5, 47, 4))
        self.assertEqual(timer.ended_at, datetime.datetime(2012, 1, 14, 5, 47, 4))

    def test_start_and_stop_timestamps(self):
        t1 = freeze_time("2012-01-14 05:47:04")
        t2 = freeze_time("2012-01-14 06:01:34")
        t1.start()
        with utils.Timer() as timer:
            t1.stop()
            t2.start()
        t2.stop()
        self.assertEqual(timer.started_at, datetime.datetime(2012, 1, 14, 5, 47, 4))
        self.assertEqual(timer.ended_at, datetime.datetime(2012, 1, 14, 6, 1, 34))

    def test_timer(self):
        with mock.patch("webnovel.utils.perf_counter", side_effect=[20.34, 45.67]) as perf_counter_mock:
            with utils.Timer() as timer:
                self.assertEqual(timer.counter_start, 20.34)
                self.assertIsNone(timer.time)
            self.assertEqual(timer.counter_end, 45.67)
            self.assertEqual(timer.time, 45.67 - 20.34)


class BatcherIterTestCase(TestCase):
    def test_empty_sequence(self):
        batches = list(utils.batcher_iter([]))
        self.assertEqual(batches, [])

    def test_sequence_is_multiple_of_batch_size(self):
        batches = list(utils.batcher_iter(range(10), batch_size=5))
        expected = [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]
        self.assertEqual(batches, expected)

    def test_sequence_is_not_a_multiple_of_batch_size(self):
        batches = list(utils.batcher_iter(range(10), batch_size=6))
        expected = [[0, 1, 2, 3, 4, 5], [6, 7, 8, 9]]
        self.assertEqual(batches, expected)

    def test_handles_iterator(self):
        batches = list(utils.batcher_iter(iter("abcdefghijk"), batch_size=4))
        expected = [["a", "b", "c", "d"], ["e", "f", "g", "h"], ["i", "j", "k"]]
        self.assertEqual(batches, expected)


class DataclassSerializationMixinTestCase(TestCase):
    def test_from_json(self):
        @dataclass
        class T(utils.DataclassSerializationMixin):
            pass

        with (mock.patch.object(T, "from_dict") as from_dict_mock, mock.patch("json.loads") as json_loads_mock):
            json_loads_mock.return_value = {"a": 1}

            T.from_json("$TEST$")

            json_loads_mock.assert_called_once_with("$TEST$")
            from_dict_mock.assert_called_once_with({"a": 1})

    def test_to_json(self):
        @dataclass
        class T(utils.DataclassSerializationMixin):
            pass

        t = T()

        with (mock.patch.object(t, "to_dict") as to_dict_mock, mock.patch("json.dumps") as dumps_mock):
            dumps_mock.return_value = "$TEST$"
            to_dict_mock.return_value = {"a": 1}

            return_value = t.to_json()

            self.assertEqual(return_value, "$TEST$")

            to_dict_mock.assert_called_once_with()
            dumps_mock.assert_called_once_with({"a": 1})

    def test_to_dict(self):
        @dataclass
        class T(utils.DataclassSerializationMixin):
            string_test: str
            integer_test: int

        t = T(string_test="$TEST$", integer_test=123)

        actual = t.to_dict()
        expected = {"string_test": "$TEST$", "integer_test": 123}

        self.assertEqual(actual, expected)

    def test_from_dict(self):
        @dataclass
        class T(utils.DataclassSerializationMixin):
            string_test: str
            integer_test: int

        actual = T.from_dict({"string_test": "$TEST$", "integer_test": 123})
        expected = T(string_test="$TEST$", integer_test=123)

        self.assertEqual(actual, expected)

    def test_from_dict_handles_ignore_unknown_fields_on(self):
        @dataclass
        class T(utils.DataclassSerializationMixin):
            ignore_unknown_fields = True

            string_test: str
            integer_test: int

        actual = T.from_dict({"string_test": "$TEST$", "integer_test": 123, "unknown_field": 341})
        expected = T(string_test="$TEST$", integer_test=123)

        self.assertEqual(actual, expected)

    def test_from_dict_handles_ignore_unknown_fields_off(self):
        @dataclass
        class T(utils.DataclassSerializationMixin):
            ignore_unknown_fields = False

            string_test: str
            integer_test: int

        with self.assertRaises(ValueError):
            T.from_dict({"string_test": "$TEST$", "integer_test": 123, "unknown_field": 341})

    def test_from_dict_handles_missing_required_fields(self):
        @dataclass
        class T(utils.DataclassSerializationMixin):
            required_fields = ["string_test", "integer_test"]

            string_test: str
            integer_test: int

        with self.assertRaises(ValueError):
            T.from_dict({"string_test": "$TEST$"})

    def test_convert_passes_unmapped_to_type(self):
        """Check that the default fall-through behaviour is to pass value to field_type."""
        self.assertNotIn(int, utils.DataclassSerializationMixin.default_type_map)
        self.assertNotIn(int, utils.DataclassSerializationMixin.import_type_map)
        actual = utils.DataclassSerializationMixin._convert("123", int)
        expected = 123
        self.assertEqual(actual, expected)

    def test_convert_uses_default_type_map(self):
        """Check that default_type_map is used if there is an entry."""
        with mock.patch.object(utils.DataclassSerializationMixin, "default_type_map", new={int: lambda x: int(x) + 1}):
            # utils.DataclassSerializationMixin.default_type_map[int] = lambda x: int(x) + 1
            self.assertIn(int, utils.DataclassSerializationMixin.default_type_map)
            self.assertNotIn(int, utils.DataclassSerializationMixin.import_type_map)
            actual = utils.DataclassSerializationMixin._convert("123", int)
            expected = 124
            self.assertEqual(actual, expected)

    def test_convert_import_type_map_overrides_default(self):
        """Check that matching entry in import_type_map overrides default_type_map."""
        with (
            mock.patch.object(utils.DataclassSerializationMixin, "default_type_map", new={int: lambda x: int(x) + 1}),
            mock.patch.object(utils.DataclassSerializationMixin, "import_type_map", new={int: lambda x: int(x) + 2}),
        ):
            # utils.DataclassSerializationMixin.default_type_map[int] = lambda x: int(x) + 1
            # utils.DataclassSerializationMixin.import_type_map[int] = lambda x: int(x) + 2
            self.assertIn(int, utils.DataclassSerializationMixin.default_type_map)
            self.assertIn(int, utils.DataclassSerializationMixin.import_type_map)
            actual = utils.DataclassSerializationMixin._convert("123", int)
            expected = 125
            self.assertEqual(actual, expected)

    def test_convert_handles_other_mixin_classes(self):
        class T(utils.DataclassSerializationMixin):
            pass

        with mock.patch.object(T, "from_dict") as from_dict:
            from_dict.return_value = "$RETURN$"
            actual = utils.DataclassSerializationMixin._convert("$INPUT$", T)
            expected = "$RETURN$"
            self.assertEqual(actual, expected)
            from_dict.assert_called_once_with("$INPUT$")
