import os
from pathlib import Path
import tempfile
from unittest import TestCase
from zipfile import ZipFile

from freezegun import freeze_time
import requests_mock

from webnovel import actions, data, epub

from .helpers import get_test_data


class SetCoverImageTestCase(TestCase):
    jpg: bytes
    png: bytes

    @classmethod
    def setUpClass(cls):
        cls.jpg: bytes = get_test_data("test-image.jpg", use_bytes=True)
        cls.png: bytes = get_test_data("test-image.png", use_bytes=True)

    @freeze_time("2001-01-01 12:15")
    def setUp(self):
        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        self.requests_mock.get("/imgs/cover-image.png", content=self.png, headers={"content-type": "image/png"})

        _, self.epub_wo_cover = tempfile.mkstemp(prefix="pywebnovel_")

        pkg = epub.EpubPackage(
            file_or_io=self.epub_wo_cover,
            options={
                "include_title_page": True,
                "include_toc_page": True,
                "include_images": True,
            },
            metadata={
                "novel_url": "https://example.com/novel/creepy-story-club",
                "site_id": "Example.com",
                "novel_id": "creepy-story-club",
                "title": "Creepy Story Club",
                "status": data.NovelStatus.ONGOING.value,
                "summary": "A\nB\nC",
                "summary_type": epub.SummaryType.text.value,
                "author": {"name": "John Smythe"},
                "cover_image_url": "https://example.com/imgs/creepy-story-club.jpg",
            },
        )
        pkg.save()

        _, self.epub_w_cover = tempfile.mkstemp(prefix="pywebnovel_")
        pkg = epub.EpubPackage(
            file_or_io=self.epub_w_cover,
            options={
                "include_title_page": True,
                "include_toc_page": True,
                "include_images": True,
            },
            metadata={
                "novel_url": "https://example.com/novel/creepy-story-club",
                "site_id": "Example.com",
                "novel_id": "creepy-story-club",
                "title": "Creepy Story Club",
                "status": data.NovelStatus.ONGOING.value,
                "summary": "A\nB\nC",
                "summary_type": epub.SummaryType.text.value,
                "author": {"name": "John Smythe"},
                "cover_image_url": "https://example.com/imgs/creepy-story-club.jpg",
            },
        )
        pkg.add_image(
            image=data.Image(url="", data=self.jpg, mimetype="image/jpeg", did_load=True),
            content=self.jpg,
            is_cover_image=True,
        )
        pkg.save()

    def tearDown(self):
        os.unlink(self.epub_wo_cover)
        os.unlink(self.epub_w_cover)

    @freeze_time("2001-01-01 12:15")
    def test_with_cover_image_url(self):
        with ZipFile(self.epub_w_cover) as zfh:
            before_file_map = {fname: zfh.read(fname) for fname in zfh.namelist()}

        actual_filenames = set(before_file_map.keys())
        expected_filenames = {
            "mimetype",
            "META-INF/container.xml",
            "OEBPS/content.opf",
            "OEBPS/toc.ncx",
            "OEBPS/stylesheet.css",
            "OEBPS/Text/cover.xhtml",
            "OEBPS/Text/nav.xhtml",
            "OEBPS/Text/title_page.xhtml",
            "OEBPS/Text/toc_page.xhtml",
            "OEBPS/Images/223f9ca11722e7eccae9eadb158fa2c7bf806ed0aa6ee4390a96df7770035ba4.jpg",
            "pywebnovel.json",
        }
        self.assertEqual(actual_filenames, expected_filenames)

        actions.set_cover_image_for_epub(
            epub_file=self.epub_w_cover, cover_image_path="https://example.com/imgs/cover-image.png"
        )

        with ZipFile(self.epub_w_cover) as zfh:
            after_file_map = {fname: zfh.read(fname) for fname in zfh.namelist()}

        #
        # Assert that the full list of files we expect to be there, are there.
        #
        actual_filenames = set(after_file_map.keys())
        expected_filenames = {
            "mimetype",
            "META-INF/container.xml",
            "OEBPS/content.opf",
            "OEBPS/toc.ncx",
            "OEBPS/stylesheet.css",
            "OEBPS/Text/cover.xhtml",
            "OEBPS/Text/nav.xhtml",
            "OEBPS/Text/title_page.xhtml",
            "OEBPS/Text/toc_page.xhtml",
            "OEBPS/Images/223f9ca11722e7eccae9eadb158fa2c7bf806ed0aa6ee4390a96df7770035ba4.jpg",
            "OEBPS/Images/0a45005663fb7dee888057d5faa903f8872b94a51767a1bfdab41c85ac3d2feb.png",
            "pywebnovel.json",
        }
        self.assertEqual(actual_filenames, expected_filenames)

        #
        # Check that the only new files are ones that we expect to be there.
        #
        actual_new_filenames = set(after_file_map.keys()) - set(before_file_map.keys())
        expected_new_filenames = {"OEBPS/Images/0a45005663fb7dee888057d5faa903f8872b94a51767a1bfdab41c85ac3d2feb.png"}
        self.assertEqual(actual_new_filenames, expected_new_filenames)

        #
        # Check that files we expect to change, did change and that the files we
        # don't expect to change remained the same.
        #
        files_expected_to_change = {
            "OEBPS/content.opf",  # new file: cover image
            "pywebnovel.json",
            "OEBPS/Text/cover.xhtml",  # reference to cover image changed
            # Note: Normally, this should change, since the timestamp would be
            #       new but since the precision of the timestamp is only down to
            #       the minutes, over the course of the test it won't change
            #       (unless we happen to cross a minute boundary). freeze_time
            #       is used so that we aren't randomly crossing minute
            #       boundaries and ended up with a sometimes failing / sometimes
            #       passing test.
            # "OEBPS/Text/title_page.xhtml",  # new timestamp for epub generation
        }
        common_filenames = set(after_file_map.keys()) & set(before_file_map.keys())

        for fname in common_filenames - files_expected_to_change:
            self.assertEqual(before_file_map[fname], after_file_map[fname], f"File {fname!r} changed unexpectedly.")

        for fname in files_expected_to_change:
            with self.subTest(fname=fname):
                self.assertNotEqual(
                    before_file_map[fname], after_file_map[fname], f"File {fname!r} did not change as expected."
                )

    @freeze_time("2001-01-01 12:15")
    def test_set_cover_image_on_epub_with_existing_cover_image(self):
        with ZipFile(self.epub_w_cover) as zfh:
            before_file_map = {fname: zfh.read(fname) for fname in zfh.namelist()}

        actual_filenames = set(before_file_map.keys())
        expected_filenames = {
            "mimetype",
            "META-INF/container.xml",
            "OEBPS/content.opf",
            "OEBPS/toc.ncx",
            "OEBPS/stylesheet.css",
            "OEBPS/Text/cover.xhtml",
            "OEBPS/Text/nav.xhtml",
            "OEBPS/Text/title_page.xhtml",
            "OEBPS/Text/toc_page.xhtml",
            "OEBPS/Images/223f9ca11722e7eccae9eadb158fa2c7bf806ed0aa6ee4390a96df7770035ba4.jpg",
            "pywebnovel.json",
        }
        self.assertEqual(actual_filenames, expected_filenames)

        actions.set_cover_image_for_epub(
            epub_file=self.epub_w_cover, cover_image_path=str(Path(__file__).parent / "data" / "test-image.png")
        )

        with ZipFile(self.epub_w_cover) as zfh:
            after_file_map = {fname: zfh.read(fname) for fname in zfh.namelist()}

        #
        # Assert that the full list of files we expect to be there, are there.
        #
        actual_filenames = set(after_file_map.keys())
        expected_filenames = {
            "mimetype",
            "META-INF/container.xml",
            "OEBPS/content.opf",
            "OEBPS/toc.ncx",
            "OEBPS/stylesheet.css",
            "OEBPS/Text/cover.xhtml",
            "OEBPS/Text/nav.xhtml",
            "OEBPS/Text/title_page.xhtml",
            "OEBPS/Text/toc_page.xhtml",
            "OEBPS/Images/223f9ca11722e7eccae9eadb158fa2c7bf806ed0aa6ee4390a96df7770035ba4.jpg",
            "OEBPS/Images/0a45005663fb7dee888057d5faa903f8872b94a51767a1bfdab41c85ac3d2feb.png",
            "pywebnovel.json",
        }
        self.assertEqual(actual_filenames, expected_filenames)

        #
        # Check that the only new files are ones that we expect to be there.
        #
        actual_new_filenames = set(after_file_map.keys()) - set(before_file_map.keys())
        expected_new_filenames = {"OEBPS/Images/0a45005663fb7dee888057d5faa903f8872b94a51767a1bfdab41c85ac3d2feb.png"}
        self.assertEqual(actual_new_filenames, expected_new_filenames)

        #
        # Check that files we expect to change, did change and that the files we
        # don't expect to change remained the same.
        #
        files_expected_to_change = {
            "OEBPS/content.opf",  # new file: cover image
            "pywebnovel.json",
            "OEBPS/Text/cover.xhtml",  # reference to cover image changed
            # Note: Normally, this should change, since the timestamp would be
            #       new but since the precision of the timestamp is only down to
            #       the minutes, over the course of the test it won't change
            #       (unless we happen to cross a minute boundary). freeze_time
            #       is used so that we aren't randomly crossing minute
            #       boundaries and ended up with a sometimes failing / sometimes
            #       passing test.
            # "OEBPS/Text/title_page.xhtml",  # new timestamp for epub generation
        }
        common_filenames = set(after_file_map.keys()) & set(before_file_map.keys())

        for fname in common_filenames - files_expected_to_change:
            self.assertEqual(before_file_map[fname], after_file_map[fname], f"File {fname!r} changed unexpectedly.")

        for fname in files_expected_to_change:
            with self.subTest(fname=fname):
                self.assertNotEqual(
                    before_file_map[fname], after_file_map[fname], f"File {fname!r} did not change as expected."
                )

    @freeze_time("2001-01-01 12:15")
    def test_set_cover_image_on_epub_with_no_cover_image(self):
        with ZipFile(self.epub_wo_cover) as zfh:
            before_file_map = {fname: zfh.read(fname) for fname in zfh.namelist()}

        actual_filenames = set(before_file_map.keys())
        expected_filenames = {
            "mimetype",
            "META-INF/container.xml",
            "OEBPS/content.opf",
            "OEBPS/toc.ncx",
            "OEBPS/stylesheet.css",
            "OEBPS/Text/nav.xhtml",
            "OEBPS/Text/title_page.xhtml",
            "OEBPS/Text/toc_page.xhtml",
            "pywebnovel.json",
        }
        self.assertEqual(actual_filenames, expected_filenames)

        actions.set_cover_image_for_epub(
            epub_file=self.epub_wo_cover, cover_image_path=str(Path(__file__).parent / "data" / "test-image.png")
        )

        with ZipFile(self.epub_wo_cover) as zfh:
            after_file_map = {fname: zfh.read(fname) for fname in zfh.namelist()}

        #
        # Assert that the full list of files we expect to be there, are there.
        #
        actual_filenames = set(after_file_map.keys())
        expected_filenames = {
            "mimetype",
            "META-INF/container.xml",
            "OEBPS/content.opf",
            "OEBPS/toc.ncx",
            "OEBPS/stylesheet.css",
            "OEBPS/Text/cover.xhtml",
            "OEBPS/Text/nav.xhtml",
            "OEBPS/Text/title_page.xhtml",
            "OEBPS/Text/toc_page.xhtml",
            "OEBPS/Images/0a45005663fb7dee888057d5faa903f8872b94a51767a1bfdab41c85ac3d2feb.png",
            "pywebnovel.json",
        }
        self.assertEqual(actual_filenames, expected_filenames)

        #
        # Check that the only new files are ones that we expect to be there.
        #
        actual_new_filenames = set(after_file_map.keys()) - set(before_file_map.keys())
        expected_new_filenames = {
            # the cover image
            "OEBPS/Images/0a45005663fb7dee888057d5faa903f8872b94a51767a1bfdab41c85ac3d2feb.png",
            # Since the original file didn't have a cover image, adding one should create a cover page.
            "OEBPS/Text/cover.xhtml",
        }
        self.assertEqual(actual_new_filenames, expected_new_filenames)

        #
        # Check that files we expect to change, did change and that the files we
        # don't expect to change remained the same.
        #
        files_expected_to_change = {
            "OEBPS/content.opf",  # new files: cover page + cover image
            "OEBPS/toc.ncx",  # addition of cover page
            "pywebnovel.json",
            "OEBPS/Text/nav.xhtml",  # addition of cover page
            "OEBPS/Text/toc_page.xhtml",  # addition of cover page
            # Note: Normally, this should change, since the timestamp would be
            #       new but since the precision of the timestamp is only down to
            #       the minutes, over the course of the test it won't change
            #       (unless we happen to cross a minute boundary). freeze_time
            #       is used so that we aren't randomly crossing minute
            #       boundaries and ended up with a sometimes failing / sometimes
            #       passing test.
            # "OEBPS/Text/title_page.xhtml",  # new timestamp for epub generation
        }
        common_filenames = set(after_file_map.keys()) & set(before_file_map.keys())

        for fname in common_filenames - files_expected_to_change:
            with self.subTest(fname=fname):
                self.assertEqual(before_file_map[fname], after_file_map[fname])

        for fname in files_expected_to_change:
            with self.subTest(fname=fname):
                self.assertNotEqual(before_file_map[fname], after_file_map[fname])

    def test_set_cover_image_handles_bad_filename(self):
        with self.assertRaises(OSError):
            actions.set_cover_image_for_epub(epub_file=self.epub_w_cover, cover_image_path="does-not-exist.png")
