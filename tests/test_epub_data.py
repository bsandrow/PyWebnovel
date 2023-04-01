from unittest import TestCase

from webnovel.epub import data


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
