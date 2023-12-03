"""Live tests for Readhive.org."""

import datetime
from unittest import TestCase

import pytest

from webnovel import data
from webnovel.sites import readhive

URL1 = "https://readhive.org/series/43151/"
URL2 = "https://readhive.org/series/43151/1/"


@pytest.mark.live
class NovelScraperTestCase(TestCase):
    maxDiff = None

    def test_title(self):
        scraper = readhive.NovelScraper()
        page = scraper.get_page(url=URL1)
        actual_title = scraper.get_title(page)
        expected_title = "The Player Hides His Past"
        self.assertEqual(actual_title, expected_title)

    def test_status(self):
        scraper = readhive.NovelScraper()
        page = scraper.get_page(url=URL1)
        actual = scraper.get_status(page)
        expected = data.NovelStatus.UNKNOWN
        self.assertEqual(actual, expected)

    def test_genres(self):
        scraper = readhive.NovelScraper()
        page = scraper.get_page(url=URL1)
        actual_genres = scraper.get_genres(page)
        expected_genres = ["Action", "Adventure"]
        self.assertEqual(actual_genres, expected_genres)

    def test_author(self):
        scraper = readhive.NovelScraper()
        page = scraper.get_page(url=URL1)
        actual = scraper.get_author(page)
        self.assertIsNone(actual)

    def test_summary(self):
        scraper = readhive.NovelScraper()
        page = scraper.get_page(url=URL1)
        actual = str(scraper.get_summary(page))
        self.assertIn("There is a secret to my strength", actual)

    def test_cover_image(self):
        scraper = readhive.NovelScraper()
        page = scraper.get_page(url=URL1)
        actual: data.Image = scraper.get_cover_image(page)
        self.assertEqual(actual.url, "/app/uploads/2023/06/9bc63e9c24d38a77be18dbd1e9fe4a62.jpeg")
        self.assertIsNone(actual.mimetype)

    def test_novel_id(self):
        scraper = readhive.NovelScraper()
        actual = scraper.get_novel_id(url=URL1)
        expected = "43151"
        self.assertEqual(actual, expected)

    def test_chapters(self):
        scraper = readhive.NovelScraper()
        page = scraper.get_page(url=URL1)
        actual = scraper.get_chapters(page=page, url=URL1)
        expected = [
            (
                "https://readhive.org/series/43151/1",
                "Chapter 1: Grandfel Claudie Arpheus Romeo",
                None,
            ),
            ("https://readhive.org/series/43151/2", "Chapter 2: If you need training (1)", None),
            ("https://readhive.org/series/43151/3", "Chapter 3: If you need training (2)", None),
            ("https://readhive.org/series/43151/4", "Chapter 4: The Demon Hunter (1)", None),
            ("https://readhive.org/series/43151/5", "Chapter 5: The Demon Hunter (2)", None),
            ("https://readhive.org/series/43151/6", "Chapter 6: Class Quest (1)", None),
        ]
        self.assertEqual([(chapter.url, chapter.title, chapter.pub_date) for chapter in actual[:6]], expected)


@pytest.mark.live
class ChapterScraperTestCase(TestCase):
    def test_process_chapter(self):
        chapter = data.Chapter(url=URL2, title="Chapter 1")
        scraper = readhive.ChapterScraper()
        scraper.process_chapter(chapter)

        # Make sure that we don't end up with nothing
        self.assertIsNotNone(chapter.original_html)
        self.assertIsNotNone(chapter.html)
        self.assertNotEqual(chapter.original_html, "")
        self.assertNotEqual(chapter.html, "")

        # Check if a known block of text that should be there exists in the
        # content.
        self.assertIn("… Nevertheless, I am screwed", chapter.original_html)
        self.assertIn("… Nevertheless, I am screwed", chapter.html)
