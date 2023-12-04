"""Live tests for SkyDemonOrder.com."""

import datetime
from unittest import TestCase

import pytest

from webnovel import data
from webnovel.sites import skydemonorder

URL1 = "https://skydemonorder.com/projects/the-genius-assassin-who-takes-it-all"
URL2 = "https://skydemonorder.com/projects/the-genius-assassin-who-takes-it-all/1-escape-1"


@pytest.mark.live
class NovelScraperTestCase(TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # NOTE: doing this here to minimize the number of times we hit the site.
        #       NovelBin is very aggressive in their anti-DDOS measures, so
        #       let's not trigger rate limiting if we don't have to.
        cls.scraper = skydemonorder.NovelScraper()
        cls.page = cls.scraper.get_page(url=URL1)

    expected_synopsis = (
        '<div class="font-l prose max-w-full py-4 text-base text-primary-600 lg:mt-0" x-data="{ isCollapsed: '
        "false, maxLength: 100, originalContent: '', content: '' }\" x-init=\"originalContent = "
        "$el.firstElementChild.innerHTML;\n        content = originalContent.length &gt; maxLength"
        " ? originalContent.substring(0, maxLength) + '…' : originalContent\">\n<span x-html=\""
        'isCollapsed ? originalContent : content"><p>Only I know this world, and now I will take it '
        "all for myself.</p>\n<p>There are no kind souls here who share generously.</p>\n<p>Only the"
        ' ruthless remain, those who devour everything alone.</p>\n</span>\n<span @click="isCollap'
        'sed = !isCollapsed" class="cursor-pointer pt-2 font-bold underline" x-show="originalCon'
        "tent.length &gt; maxLength\" x-text=\"isCollapsed ? 'Less' : 'More'\"></span>\n</div>"
    )

    def test_novel(self):
        novel = self.scraper.scrape(URL1)
        self.assertEqual(novel.title, "The Genius Assassin Who Takes it All")
        self.assertEqual(novel.status, data.NovelStatus.ONGOING)
        self.assertEqual(novel.summary, self.scraper.get_summary(self.page))
        self.assertIsNone(novel.genres)
        self.assertIsNone(novel.author)
        self.assertIsNone(novel.tags)
        self.assertGreaterEqual(len(novel.chapters), 24)
        self.assertIsNotNone(novel.published_on)
        self.assertIn("Views", novel.extras)

        # Check the "release_schedule" extras
        self.assertIn("release_schedule", novel.extras)
        self.assertGreater(len(novel.extras), 0)
        self.assertTrue(all(ch["release_date"] > datetime.datetime.today() for ch in novel.extras["release_schedule"]))

    def test_title(self):
        actual_title = self.scraper.get_title(self.page)
        expected_title = "The Genius Assassin Who Takes it All"
        self.assertEqual(actual_title, expected_title)

    def test_status(self):
        actual = self.scraper.get_status(self.page)
        expected = data.NovelStatus.ONGOING
        self.assertEqual(actual, expected)

    def test_genres(self):
        actual = self.scraper.get_genres(self.page)
        self.assertIsNone(actual)

    def test_author(self):
        actual = self.scraper.get_author(self.page)
        self.assertIsNone(actual)

    def test_summary(self):
        actual = str(self.scraper.get_summary(self.page))
        self.assertEqual(actual, self.expected_synopsis)

    def test_cover_image(self):
        actual: data.Image = self.scraper.get_cover_image(self.page)
        self.assertEqual(
            actual.url,
            "https://skydemonorder.nyc3.cdn.digitaloceanspaces.com/covers/36JgwC5VdwvknSFQpuN96r3EaKIwjNcSjVL5FqD7.jpg",
        )
        self.assertIsNone(actual.mimetype)

    def test_novel_id(self):
        scraper = skydemonorder.NovelScraper()
        actual = scraper.get_novel_id(url=URL1)
        expected = "the-genius-assassin-who-takes-it-all"
        self.assertEqual(actual, expected)

    def test_chapters(self):
        actual = self.scraper.get_chapters(page=self.page, url=URL1)
        expected = [
            (
                "https://skydemonorder.com/projects/the-genius-assassin-who-takes-it-all/1-escape-1",
                "Ep.1: Escape (1)",
                datetime.datetime(2023, 11, 25, 0, 0),
            ),
            (
                "https://skydemonorder.com/projects/the-genius-assassin-who-takes-it-all/2-escape-2",
                "Ep.2: Escape (2)",
                datetime.datetime(2023, 11, 25, 0, 0),
            ),
            (
                "https://skydemonorder.com/projects/the-genius-assassin-who-takes-it-all/3-escape-3",
                "Ep.3: Escape (3)",
                datetime.datetime(2023, 11, 25, 0, 0),
            ),
            (
                "https://skydemonorder.com/projects/the-genius-assassin-who-takes-it-all/4-the-client-1",
                "Ep.4: The Client (1)",
                datetime.datetime(2023, 11, 25, 0, 0),
            ),
            (
                "https://skydemonorder.com/projects/the-genius-assassin-who-takes-it-all/5-the-client-2",
                "Ep.5: The Client (2)",
                datetime.datetime(2023, 11, 25, 0, 0),
            ),
            (
                "https://skydemonorder.com/projects/the-genius-assassin-who-takes-it-all/6-the-client-3",
                "Ep.6: The Client (3)",
                datetime.datetime(2023, 11, 25, 0, 0),
            ),
        ]
        self.assertEqual([(chapter.url, chapter.title, chapter.pub_date) for chapter in actual[:6]], expected)
        self.assertGreaterEqual(len(actual), 24)


@pytest.mark.live
class ChapterScraperTestCase(TestCase):
    def test_process_chapter(self):
        chapter = data.Chapter(url=URL2, title="Ep.1: Escape (1)")
        scraper = skydemonorder.ChapterScraper()
        scraper.process_chapter(chapter)

        # Make sure that we don't end up with nothing
        self.assertIsNotNone(chapter.original_html)
        self.assertIsNotNone(chapter.html)
        self.assertNotEqual(chapter.original_html, "")
        self.assertNotEqual(chapter.html, "")

        # Check if a known block of text that should be there exists in the
        # content.
        self.assertIn("“Kang-hoo, are you okay?”", chapter.original_html)
        self.assertIn("“Kang-hoo, are you okay?”", chapter.html)

        self.assertIn(
            "[Shin Kang-hoo should have decided to escape from Cheongmyeong Detention Center that day.",
            chapter.original_html,
        )
        self.assertIn(
            "[Shin Kang-hoo should have decided to escape from Cheongmyeong Detention Center that day.", chapter.html
        )

        # Make sure that there aren't any changes to this class
        self.assertIn("novel-system-box", chapter.original_html)
        self.assertIn("novel-system-box", chapter.html)
