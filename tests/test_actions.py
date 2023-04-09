from contextlib import contextmanager
import os
from pathlib import Path
import tempfile
from typing import Iterable, Optional
from unittest import TestCase
from zipfile import ZipFile

from freezegun import freeze_time
import requests_mock

from webnovel import actions, data, epub

from .helpers import get_test_data


class ActionTestCaseMixin(TestCase):
    @staticmethod
    def create_epub(jpg: bytes = None, timestamp: str = "2001-01-01 12:15"):
        _, epubfile = tempfile.mkstemp(prefix="pywebnovel_")
        pkg = epub.EpubPackage(
            file_or_io=epubfile,
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

        if jpg:
            pkg.add_image(
                image=data.Image(url="", data=jpg, mimetype="image/jpeg", did_load=True),
                content=jpg,
                is_cover_image=True,
            )

        with freeze_time(timestamp):
            pkg.save()

        return epubfile

    @contextmanager
    def assert_files_changed(
        self,
        epub_file: str,
        expected_changed_files: Iterable,
        expected_new_files: Optional[Iterable] = None,
        expected_initial_files: Optional[Iterable] = None,
        expected_final_files: Optional[Iterable] = None,
    ):

        # NOTE: The explicit test for None when choosing to do assertions is a
        # speicfic choice, which allows empty iterables to be passed when the
        # expected set of files is an empty set.

        expected_changed_files = set(expected_changed_files) if expected_changed_files is not None else None
        expected_new_files = set(expected_new_files) if expected_new_files is not None else None
        expected_initial_files = set(expected_initial_files) if expected_initial_files is not None else None
        expected_final_files = set(expected_final_files) if expected_final_files is not None else None

        with ZipFile(epub_file) as zfh:
            pre_file_map = {fname: zfh.read(fname) for fname in zfh.namelist()}
            pre_files = set(pre_file_map.keys())

        #
        # If expected_initial_files was provided, assert it.
        #
        if expected_initial_files is not None:
            self.assertEqual(pre_files, expected_initial_files)

        yield

        with ZipFile(epub_file) as zfh:
            post_file_map = {fname: zfh.read(fname) for fname in zfh.namelist()}
            post_files = set(post_file_map.keys())

        #
        # If expected_final_files was provided, assert that the full list of
        # files in post_file_map looks like it.
        #
        if expected_final_files is not None:
            self.assertEqual(post_files, expected_final_files)

        #
        # If expected_new_files was provided, assert that these files are only
        # present in post_files.
        #
        if expected_new_files is not None:
            actual_new_files = post_files - pre_files
            self.assertEqual(actual_new_files, expected_new_files)

        common_files = pre_files & post_files

        #
        # Make sure that all files we expect to have changes were present both
        # before _and_ after the change. expected_new_files should be used to
        # assert files that were expected to only be present in the
        # post_file_map.
        #
        self.assertEqual(
            expected_changed_files - common_files,
            set(),
            (
                f"Files that were expected to change where not present either in "
                f"the package before or after the change: {expected_changed_files - common_files}"
            ),
        )

        #
        # Assert that all files expected to change did _not_ remain the same.
        #
        for filename in common_files - expected_changed_files:
            self.assertEqual(
                pre_file_map[filename],
                post_file_map[filename],
                (
                    f"\n"
                    f"File {filename} unexpectedly had changes to content.\n\n"
                    f"==[ Before ]==\n\n"
                    f"{pre_file_map[filename]!r}\n\n"
                    f"==[ After  ]==\n\n"
                    f"{post_file_map[filename]!r}\n\n"
                    f"==============\n"
                ),
            )

        #
        # Assert that all files that were _not_ expected to change actually
        # remained the same.
        #
        for filename in expected_changed_files:
            self.assertNotEqual(
                pre_file_map[filename],
                post_file_map[filename],
                (
                    f"\n"
                    f"File {filename} was expected to change, but didn't\n\n"
                    f"==[ Contents ]==\n\n"
                    f"{pre_file_map[filename]!r}\n\n"
                    f"==============\n"
                ),
            )


class RebuildTestCase(ActionTestCaseMixin, TestCase):
    jpg: bytes

    @classmethod
    def setUpClass(cls):
        cls.jpg: bytes = get_test_data("test-image.jpg", use_bytes=True)

    def setUp(self):
        self.epub = self.create_epub(jpg=self.jpg)

    def tearDown(self):
        os.unlink(self.epub_wo_cover)
        os.unlink(self.epub_w_cover)

    def test_rebuild_action(self):
        with self.assert_files_changed(self.epub, expected_changed_files={"OEBPS/Text/title_page.xhtml"}):
            actions.rebuild(self.epub)


class SetCoverImageTestCase(ActionTestCaseMixin, TestCase):
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

        self.epub_wo_cover = self.create_epub()
        self.epub_w_cover = self.create_epub(jpg=self.jpg)

    def tearDown(self):
        os.unlink(self.epub_wo_cover)
        os.unlink(self.epub_w_cover)

    @freeze_time("2001-01-01 12:15")
    def test_with_cover_image_url(self):
        with self.assert_files_changed(
            self.epub_w_cover,
            expected_changed_files={
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
            },
            expected_initial_files={
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
            },
            expected_new_files={"OEBPS/Images/0a45005663fb7dee888057d5faa903f8872b94a51767a1bfdab41c85ac3d2feb.png"},
        ):
            actions.set_cover_image_for_epub(
                epub_file=self.epub_w_cover, cover_image_path="https://example.com/imgs/cover-image.png"
            )

        #
        # Check that the EpubMetadata.cover_image_url has changed.
        #
        pkg = epub.EpubPackage.load(self.epub_w_cover)
        self.assertEqual(pkg.metadata.cover_image_url, "https://example.com/imgs/cover-image.png")

    @freeze_time("2001-01-01 12:15")
    def test_set_cover_image_on_epub_with_existing_cover_image(self):
        with self.assert_files_changed(
            self.epub_w_cover,
            expected_initial_files={
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
            },
            expected_new_files={"OEBPS/Images/0a45005663fb7dee888057d5faa903f8872b94a51767a1bfdab41c85ac3d2feb.png"},
            expected_changed_files={
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
            },
        ):
            actions.set_cover_image_for_epub(
                epub_file=self.epub_w_cover, cover_image_path=str(Path(__file__).parent / "data" / "test-image.png")
            )

    @freeze_time("2001-01-01 12:15")
    def test_set_cover_image_on_epub_with_no_cover_image(self):
        with self.assert_files_changed(
            self.epub_wo_cover,
            expected_initial_files={
                "mimetype",
                "META-INF/container.xml",
                "OEBPS/content.opf",
                "OEBPS/toc.ncx",
                "OEBPS/stylesheet.css",
                "OEBPS/Text/nav.xhtml",
                "OEBPS/Text/title_page.xhtml",
                "OEBPS/Text/toc_page.xhtml",
                "pywebnovel.json",
            },
            expected_final_files={
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
            },
            expected_new_files={
                # the cover image
                "OEBPS/Images/0a45005663fb7dee888057d5faa903f8872b94a51767a1bfdab41c85ac3d2feb.png",
                # Since the original file didn't have a cover image, adding one should create a cover page.
                "OEBPS/Text/cover.xhtml",
            },
            expected_changed_files={
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
            },
        ):
            actions.set_cover_image_for_epub(
                epub_file=self.epub_wo_cover, cover_image_path=str(Path(__file__).parent / "data" / "test-image.png")
            )

    def test_set_cover_image_handles_bad_filename(self):
        with self.assertRaises(OSError):
            actions.set_cover_image_for_epub(epub_file=self.epub_w_cover, cover_image_path="does-not-exist.png")
