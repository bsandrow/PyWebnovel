from collections import defaultdict
from io import BytesIO, TextIOWrapper
from unittest import TestCase

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
