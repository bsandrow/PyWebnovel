import os
from pathlib import Path
from unittest import mock

from bs4 import BeautifulSoup
from freezegun import freeze_time

from webnovel import actions, data, epub, errors

from .helpers import TestCase, get_test_data


class RebuildTestCase(TestCase):
    jpg: bytes
    epub: str

    mocked_requests = {
        "/n/creepy-story-club/chapter-1/": (
            """
            <div>
            <div id="chr-content">
                <p>Lorem ipsum dolor sit amet. Quo quas commodi ut quod vitae
                33 maiores soluta et provident nostrum. Eum nulla
                necessitatibus qui perspiciatis voluptate eum maxime galisum
                est obcaecati molestias aut labore cupiditate eum blanditiis
                doloremque. </p>
                <p>Qui labore architecto est dolore quibusdam et consequatur
                vitae sed voluptate consectetur aut beatae eveniet sed nihil
                nihil. Sed obcaecati vero in consequatur galisum quo veritatis
                dicta et pariatur reprehenderit. Non voluptatem voluptas qui
                illum nesciunt aut optio quibusdam non enim esse.</p>
                <p>Aut totam assumenda ea necessitatibus molestiae ut incidunt
                incidunt. Est dolorum repellendus 33 excepturi nulla ea atque
                illum 33 temporibus optio. 33 quia ullam et quis laudantium qui
                facere culpa.</p>
            </div>
            </div>
            """
        ),
        "/n/creepy-story-club/chapter-2/": (
            """
            <div>
            <div id="chr-content">
                <p>Lorem ipsum dolor sit amet. Quo quas commodi ut quod vitae
                33 maiores soluta et provident nostrum. Eum nulla
                necessitatibus qui perspiciatis voluptate eum maxime galisum
                est obcaecati molestias aut labore cupiditate eum blanditiis
                doloremque. </p>
                <p>Qui labore architecto est dolore quibusdam et consequatur
                vitae sed voluptate consectetur aut beatae eveniet sed nihil
                nihil. Sed obcaecati vero in consequatur galisum quo veritatis
                dicta et pariatur reprehenderit. Non voluptatem voluptas qui
                illum nesciunt aut optio quibusdam non enim esse.</p>
                <p>Aut totam assumenda ea necessitatibus molestiae ut incidunt
                incidunt. Est dolorum repellendus 33 excepturi nulla ea atque
                illum 33 temporibus optio. 33 quia ullam et quis laudantium qui
                facere culpa.</p>
            </div>
            </div>
            """
        ),
        "/n/creepy-story-club/chapter-14/": (
            """
            <div>
            <div id="chr-content">
                <p>Lorem ipsum dolor sit amet. Quo quas commodi ut quod vitae
                33 maiores soluta et provident nostrum. Eum nulla
                necessitatibus qui perspiciatis voluptate eum maxime galisum
                est obcaecati molestias aut labore cupiditate eum blanditiis
                doloremque. </p>
                <p>Qui labore architecto est dolore quibusdam et consequatur
                vitae sed voluptate consectetur aut beatae eveniet sed nihil
                nihil. Sed obcaecati vero in consequatur galisum quo veritatis
                dicta et pariatur reprehenderit. Non voluptatem voluptas qui
                illum nesciunt aut optio quibusdam non enim esse.</p>
                <p>Aut totam assumenda ea necessitatibus molestiae ut incidunt
                incidunt. Est dolorum repellendus 33 excepturi nulla ea atque
                illum 33 temporibus optio. 33 quia ullam et quis laudantium qui
                facere culpa.</p>
            </div>
            </div>
            """
        ),
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.jpg: bytes = get_test_data("test-image.jpg", use_bytes=True)

    def setUp(self):
        super().setUp()
        self.epub = self.create_epub(jpg=self.jpg)

    def tearDown(self):
        super().tearDown()
        os.unlink(self.epub)

    def add_chapters_to_epub(self):
        chapters = [
            data.Chapter(
                url="https://novelbin.net/n/creepy-story-club/chapter-1/",
                slug="chapter-1",
                chapter_no=1,
                html=(
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
                url="https://novelbin.net/n/creepy-story-club/chapter-2/",
                slug="chapter-2",
                chapter_no=2,
                html=(
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
                url="https://novelbin.net/n/creepy-story-club/chapter-14/",
                slug="chapter-14",
                chapter_no=14,
                html=(
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

        with freeze_time("2009-01-01 11:41"):
            pkg = epub.EpubPackage.load(self.epub)
            for chapter in chapters:
                pkg.add_chapter(chapter)
            pkg.save()

    def test_rebuild_action(self):
        with self.assert_files_changed(
            self.epub, expected_changed_files={"OEBPS/content.opf", "OEBPS/Text/title_page.xhtml"}
        ):
            actions.App().rebuild(self.epub)

    def test_reload_chapters(self):
        self.add_chapters_to_epub()

        with self.assert_files_changed(
            self.epub,
            expected_initial_files={
                "META-INF/container.xml",
                "OEBPS/Images/223f9ca11722e7eccae9eadb158fa2c7bf806ed0aa6ee4390a96df7770035ba4.jpg",
                "OEBPS/Text/ch00001.xhtml",
                "OEBPS/Text/ch00002.xhtml",
                "OEBPS/Text/ch00003.xhtml",
                "OEBPS/Text/cover.xhtml",
                "OEBPS/Text/nav.xhtml",
                "OEBPS/Text/title_page.xhtml",
                "OEBPS/Text/toc_page.xhtml",
                "OEBPS/content.opf",
                "OEBPS/stylesheet.css",
                "OEBPS/toc.ncx",
                "mimetype",
                "pywebnovel.json",
            },
            expected_changed_files={
                "OEBPS/content.opf",
                "OEBPS/Text/ch00001.xhtml",
                "OEBPS/Text/title_page.xhtml",
                "pywebnovel.json",
            },
        ):
            actions.App().rebuild(self.epub, reload_chapters=["chapter-1"])

    def test_reload_chapters_handles_multiple_chapters(self):
        self.add_chapters_to_epub()

        with self.assert_files_changed(
            self.epub,
            expected_initial_files={
                "META-INF/container.xml",
                "OEBPS/Images/223f9ca11722e7eccae9eadb158fa2c7bf806ed0aa6ee4390a96df7770035ba4.jpg",
                "OEBPS/Text/ch00001.xhtml",
                "OEBPS/Text/ch00002.xhtml",
                "OEBPS/Text/ch00003.xhtml",
                "OEBPS/Text/cover.xhtml",
                "OEBPS/Text/nav.xhtml",
                "OEBPS/Text/title_page.xhtml",
                "OEBPS/Text/toc_page.xhtml",
                "OEBPS/content.opf",
                "OEBPS/stylesheet.css",
                "OEBPS/toc.ncx",
                "mimetype",
                "pywebnovel.json",
            },
            expected_changed_files={
                "OEBPS/content.opf",
                "OEBPS/Text/ch00001.xhtml",
                "OEBPS/Text/ch00002.xhtml",
                "OEBPS/Text/ch00003.xhtml",
                "OEBPS/Text/title_page.xhtml",
                "pywebnovel.json",
            },
        ):
            actions.App().rebuild(self.epub, reload_chapters=["chapter-1", "chapter-2", "chapter-14"])

    def test_reload_chapters_ignores_bad_slug(self):
        self.add_chapters_to_epub()

        with self.assert_files_changed(
            self.epub,
            expected_initial_files={
                "META-INF/container.xml",
                "OEBPS/Images/223f9ca11722e7eccae9eadb158fa2c7bf806ed0aa6ee4390a96df7770035ba4.jpg",
                "OEBPS/Text/ch00001.xhtml",
                "OEBPS/Text/ch00002.xhtml",
                "OEBPS/Text/ch00003.xhtml",
                "OEBPS/Text/cover.xhtml",
                "OEBPS/Text/nav.xhtml",
                "OEBPS/Text/title_page.xhtml",
                "OEBPS/Text/toc_page.xhtml",
                "OEBPS/content.opf",
                "OEBPS/stylesheet.css",
                "OEBPS/toc.ncx",
                "mimetype",
                "pywebnovel.json",
            },
            expected_changed_files={
                "OEBPS/content.opf",
                "OEBPS/Text/ch00001.xhtml",
                "OEBPS/Text/ch00002.xhtml",
                "OEBPS/Text/ch00003.xhtml",
                "OEBPS/Text/title_page.xhtml",
                "pywebnovel.json",
            },
        ):
            actions.App().rebuild(self.epub, reload_chapters=["chapter-1", "chapter-2", "chapter-33", "chapter-14"])


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
        super().setUp()
        self.requests_mock.get("/imgs/cover-image.png", content=self.png, headers={"content-type": "image/png"})
        self.epub_wo_cover = self.create_epub()
        self.epub_w_cover = self.create_epub(jpg=self.jpg)

    def tearDown(self):
        super().tearDown()
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
            actions.App().set_cover_image_for_epub(
                filename=self.epub_w_cover, cover_image="https://example.com/imgs/cover-image.png"
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
            actions.App().set_cover_image_for_epub(
                filename=self.epub_w_cover, cover_image=str(Path(__file__).parent / "data" / "test-image.png")
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
            actions.App().set_cover_image_for_epub(
                filename=self.epub_wo_cover, cover_image=str(Path(__file__).parent / "data" / "test-image.png")
            )

    def test_set_cover_image_handles_bad_filename(self):
        with self.assertRaises(OSError):
            actions.App().set_cover_image_for_epub(filename=self.epub_w_cover, cover_image="does-not-exist.png")


class UpdateEbookTestCase(TestCase):
    def test_handles_ebook_with_no_novel_url(self):
        with mock.patch("webnovel.actions.epub.EpubPackage.load") as load_mock:
            mock_pkg = load_mock.return_value = mock.MagicMock()
            mock_pkg.metadata.novel_url = None
            with self.assertRaises(ValueError):
                actions.App().update("test", limit=10)

    def test_handles_no_matching_scraper(self):
        epub = self.create_epub()
        with self.assertRaises(errors.NoMatchingNovelScraper):
            actions.App().update(epub, limit=10)

    def test_handles_orphaned_urls(self):
        with (
            mock.patch("webnovel.actions.epub.EpubPackage.load") as load_mock,
            mock.patch("webnovel.sites.novelbin.NovelBinScraper.scrape") as scrape_mock,
        ):
            load_mock.return_value = epub = mock.MagicMock()
            epub.metadata.novel_url = "https://novelbin.net/n/creepy-story-club-redux"
            scrape_mock.return_value = novel_mock = mock.Mock()
            novel_mock.chapters = [
                mock.Mock(url="https://example.com/chapter/1"),
                mock.Mock(url="https://example.com/chapter/3"),
            ]
            epub.chapters = {
                "https://example.com/chapter/1": 1,
                "https://example.com/chapter/2": 2,
                "https://example.com/chapter/3": 3,
            }
            with self.assertRaises(errors.OrphanedUrlsError):
                actions.App().update(epub, limit=10)

    def test_handles_no_new_chapters(self):
        with (
            mock.patch("webnovel.actions.epub.EpubPackage.load") as load_mock,
            mock.patch("webnovel.sites.novelbin.NovelBinScraper.scrape") as scrape_mock,
        ):
            load_mock.return_value = epub = mock.MagicMock()
            epub.metadata.novel_url = "https://novelbin.net/n/creepy-story-club-redux"
            scrape_mock.return_value = novel_mock = mock.Mock()
            novel_mock.chapters = [
                mock.Mock(url="https://example.com/chapter/1"),
                mock.Mock(url="https://example.com/chapter/3"),
            ]
            epub.chapters = {"https://example.com/chapter/1": 1, "https://example.com/chapter/3": 3}
            result = actions.App().update(epub, limit=10)
            self.assertEqual(result, 0)

    def test_handles_nonsequential_chapters(self):
        with (
            mock.patch("webnovel.actions.epub.EpubPackage.load") as load_mock,
            mock.patch("webnovel.sites.novelbin.NovelBinScraper.scrape") as scrape_mock,
        ):
            load_mock.return_value = epub = mock.MagicMock()
            epub.metadata.novel_url = "https://novelbin.net/n/creepy-story-club-redux"
            scrape_mock.return_value = novel_mock = mock.Mock()
            novel_mock.chapters = [
                mock.Mock(chapter_no=0, url="https://example.com/chapter/1"),
                mock.Mock(chapter_no=1, url="https://example.com/chapter/2"),
                mock.Mock(chapter_no=2, url="https://example.com/chapter/3"),
            ]
            epub.chapters = {
                "https://example.com/chapter/1": mock.Mock(chapter_no=0, url="https://example.com/chapter/1"),
                # "https://example.com/chapter/2": mock.Mock(chapter_no=1, url="https://example.com/chapter/2"),
                "https://example.com/chapter/3": mock.Mock(chapter_no=2, url="https://example.com/chapter/3"),
            }
            with self.assertRaises(errors.NonsequentialChaptersError):
                result = actions.App().update(epub, limit=10)

    def test_handles_limit(self):
        with (
            mock.patch("webnovel.actions.epub.EpubPackage.load") as load_mock,
            mock.patch("webnovel.sites.novelbin.NovelBinScraper.scrape") as scrape_mock,
        ):
            load_mock.return_value = epub = mock.MagicMock()
            epub.metadata.novel_url = "https://novelbin.net/n/creepy-story-club-redux"
            scrape_mock.return_value = novel_mock = mock.Mock()
            novel_mock.chapters = [mock.Mock(chapter_no=i, url=f"https://example.com/chapter/{i+1}") for i in range(10)]
            epub.chapters = {
                f"https://example.com/chapter/{i+1}": mock.Mock(chapter_no=i, url="https://example.com/chapter/{i+1}")
                for i in range(3)
            }
            app = actions.App()
            with mock.patch.object(app, "add_chapters") as add_ch_mock:
                result = app.update(epub)

            epub.save.assert_called_once_with()
            add_ch_mock.assert_called_once_with(ebook=epub, chapters=novel_mock.chapters[3:], batch_size=20)
