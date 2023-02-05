from unittest import TestCase

from webnovel.epub.data import EpubNovel
from webnovel.epub.files import PyWebNovelJSON
from webnovel.epub.pkg import EpubPackage


class PyWebNovelJSONTestCase(TestCase):
    def test_attributes(self):
        pkg = EpubPackage(filename="test.epub", novel=EpubNovel(url="URL", title="TITLE"))
        pwn_json = PyWebNovelJSON(pkg)
        self.assertEqual(pwn_json.file_id, "pywebnovel-meta")
        self.assertEqual(pwn_json.filename, "pywebnovel.json")
        self.assertEqual(pwn_json.mimetype, "application/json")
        self.assertIsNone(pwn_json.title)
        self.assertFalse(pwn_json.include_in_spine)
        self.assertIsNone(pwn_json.data)
