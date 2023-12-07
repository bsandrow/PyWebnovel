from unittest import TestCase, mock

from webnovel import errors
from webnovel.epub import data


class MetadataVersioningTestCase(TestCase):
    def test_get_version_handles_missing_version(self):
        actual = data.EpubMetadata.detect_version({})
        expected = data.MetadataVersion.v1
        self.assertEqual(actual, expected)

    def test_get_version_handles_good_values(self):
        actual = data.EpubMetadata.detect_version({"version": 1})
        expected = data.MetadataVersion.v1
        self.assertEqual(actual, expected)

        actual = data.EpubMetadata.detect_version({"version": 2})
        expected = data.MetadataVersion.v2
        self.assertEqual(actual, expected)

        actual = data.EpubMetadata.detect_version({"version": "2"})
        expected = data.MetadataVersion.v2
        self.assertEqual(actual, expected)

    def test_get_version_handles_bad_values(self):
        with self.assertRaises(errors.EpubParseError):
            data.EpubMetadata.detect_version({"version": "ABC"})

        with self.assertRaises(errors.EpubParseError):
            data.EpubMetadata.detect_version({"version": ""})

    def test_uses_default_version(self):
        metadata = data.EpubMetadata("NOVEL_URL", "NOVEL_ID", "SITE_ID")
        actual = metadata.version
        expected = data.EpubMetadata.CURRENT_VERSION
        self.assertEqual(actual, expected)

    @mock.patch("webnovel.epub.data.EpubMetadata.convert_to_version")
    def test_convert_to_current_version(self, convert_to_version_mock):
        _data = {}
        data.EpubMetadata.convert_to_current_version(_data)
        convert_to_version_mock.assert_called_once_with(_data, data.EpubMetadata.CURRENT_VERSION)

    def test_build_conversion_path(self):
        def _c(data):
            data = dict(data)
            data["version"] = "2"
            data["1"] = True
            return data

        data.EpubMetadata.VERSION_CONVERSION_MAP[data.MetadataVersion.v1] = _c

        actual = data.EpubMetadata.build_conversion_path(
            data={"version": "1", "title": "$TITLE$"},
            target_version=data.MetadataVersion.v2,
        )
        expected = [_c]
        self.assertEqual(actual, expected)

    def test_convert_to_version(self):
        def _c(data):
            data = dict(data)
            data["version"] = "2"
            data["1"] = True
            return data

        data.EpubMetadata.VERSION_CONVERSION_MAP[data.MetadataVersion.v1] = _c

        actual = data.EpubMetadata.convert_to_version(
            data={"version": "1", "title": "$TITLE$"},
            target_version=data.MetadataVersion.v2,
        )
        expected = {
            "version": "2",
            "title": "$TITLE$",
            "1": True,
        }
        self.assertEqual(actual, expected)

    def test_convert_to_current_version(self):
        with mock.patch("webnovel.epub.data.EpubMetadata.convert_to_version") as m:
            _data = {}
            data.EpubMetadata.convert_to_current_version(_data)
            m.assert_called_once_with(_data, data.EpubMetadata.CURRENT_VERSION)


class EpubOptionsTestCase(TestCase):
    def test_to_dict_and_from_dict(self):
        options = data.EpubOptions()
        expected = data.EpubOptions()
        actual = data.EpubOptions.from_dict(options.to_dict())
        self.assertEqual(actual, expected)


class EpubMetadataTestCase(TestCase):
    def test_to_dict_and_from_dict(self):
        metadata = data.EpubMetadata(novel_url="A", novel_id="B", site_id="C")
        expected = data.EpubMetadata(novel_url="A", novel_id="B", site_id="C")
        actual = data.EpubMetadata.from_dict(metadata.to_dict())
        self.assertEqual(actual, expected)
