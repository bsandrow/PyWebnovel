from contextlib import contextmanager
import os
from pathlib import Path
import tempfile
from typing import Iterable, Optional
from zipfile import ZipFile

from bs4 import BeautifulSoup
from freezegun import freeze_time
import requests_mock

from webnovel import actions, data, epub

from .helpers import TestCase, get_test_data


class RebuildTestCase(TestCase):
    jpg: bytes
    epub: str

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.jpg: bytes = get_test_data("test-image.jpg", use_bytes=True)

    def setUp(self):
        self.epub = self.create_epub(jpg=self.jpg)

    def tearDown(self):
        os.unlink(self.epub)

    def test_rebuild_action(self):
        with self.assert_files_changed(self.epub, expected_changed_files={"OEBPS/Text/title_page.xhtml"}):
            actions.rebuild(self.epub)

    def test_reload_chapters(self):
        chapters = [
            data.Chapter(
                url="https://wuxiaworld.site/novel/creepy-story-club/chapter-1/",
                slug="chapter-1",
                chapter_no=1,
                html_content=BeautifulSoup(
                    """
                    <div>
                    <p>Lorem ipsum dolor sit amet. Quo quas commodi ut quod vitae
                    33 maiores soluta et provident nostrum. Eum nulla
                    necessitatibus qui perspiciatis voluptate eum maxime galisum
                    est obcaecati molestias aut labore cupiditate eum blanditiis
                    doloremque. </p>
                    </div>
                    """
                ),
            ),
            data.Chapter(
                url="https://wuxiaworld.site/novel/creepy-story-club/chapter-2/",
                slug="chapter-2",
                chapter_no=2,
                html_content=BeautifulSoup(
                    """
                    <div>
                    <p>Lorem ipsum dolor sit amet. Quo quas commodi ut quod vitae
                    33 maiores soluta et provident nostrum. Eum nulla
                    necessitatibus qui perspiciatis voluptate eum maxime galisum
                    est obcaecati molestias aut labore cupiditate eum blanditiis
                    doloremque. </p>
                    </div>
                    """
                ),
            ),
            data.Chapter(
                url="https://wuxiaworld.site/novel/creepy-story-club/chapter-14/",
                slug="chapter-14",
                chapter_no=14,
                html_content=BeautifulSoup(
                    """
                    <div>
                    <p>Lorem ipsum dolor sit amet. Quo quas commodi ut quod vitae
                    33 maiores soluta et provident nostrum. Eum nulla
                    necessitatibus qui perspiciatis voluptate eum maxime galisum
                    est obcaecati molestias aut labore cupiditate eum blanditiis
                    doloremque. </p>
                    </div>
                    """
                ),
            ),
        ]

        pkg = epub.EpubPackage.load(self.epub)
        for chapter in chapters:
            pkg.add_chapter(chapter)
        pkg.save()

        with self.assert_files_changed(self.epub, expected_changed_files={"OEBPS/Text/title_page.xhtml"}):
            actions.rebuild(
                self.epub,
            )


class SetCoverImageTestCase(TestCase):
    jpg: bytes
    png: bytes

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
