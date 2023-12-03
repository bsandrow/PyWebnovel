"""Live tests for Helscans.com."""

import datetime
from unittest import TestCase

import pytest

from webnovel import data
from webnovel.sites import helscans

URL1 = "https://helscans.com/manga/theatrical-regression-life/"
URL2 = "https://helscans.com/theatrical-regression-life-chapter-2/"


@pytest.mark.live
class NovelScraperTestCase(TestCase):
    maxDiff = None

    expected_synopsis = (
        '<div class="entry-content entry-content-single" id="synopsis"'
        ' itemprop="description" style="white-space: pre-line; width: 100%;">\n'
        "						A theatrical regression life of an old-fashioned "
        "villain who recalled his past life.\n"
        "\n"
        "\"There's nothing I won't do for a better life.\"\n"
        "\n"
        "———\n"
        "\n"
        "Survival in the ‘Otherworld’; a place where only the insane can set foot in.\n"
        "\n"
        " \n"
        "            </div>"
    )

    def test_title(self):
        scraper = helscans.NovelScraper()
        page = scraper.get_page(url=URL1)
        actual_title = scraper.get_title(page)
        expected_title = "Theatrical Regression Life"
        self.assertEqual(actual_title, expected_title)

    def test_status(self):
        scraper = helscans.NovelScraper()
        page = scraper.get_page(url=URL1)
        actual = scraper.get_status(page)
        expected = data.NovelStatus.ONGOING
        self.assertEqual(actual, expected)

    def test_genres(self):
        scraper = helscans.NovelScraper()
        page = scraper.get_page(url=URL1)
        actual_genres = scraper.get_genres(page)
        expected_genres = ["Fantasy", "Genius MC", "Regression", "Villain"]
        self.assertEqual(actual_genres, expected_genres)

    def test_author(self):
        scraper = helscans.NovelScraper()
        page = scraper.get_page(url=URL1)
        actual = scraper.get_author(page)
        expected = data.Person(name="취미글주의", email=None, url=None)
        self.assertEqual(actual, expected)

    def test_summary(self):
        scraper = helscans.NovelScraper()
        page = scraper.get_page(url=URL1)
        actual = str(scraper.get_summary(page))
        self.assertEqual(actual, self.expected_synopsis)

    def test_novel_id(self):
        scraper = helscans.NovelScraper()
        actual = scraper.get_novel_id(url=URL1)
        expected = "theatrical-regression-life"
        self.assertEqual(actual, expected)

    def test_chapters(self):
        scraper = helscans.NovelScraper()
        page = scraper.get_page(url=URL1)
        actual = scraper.get_chapters(page=page, url=URL1)
        expected = [
            (
                "https://helscans.com/theatrical-regression-life-prologue/",
                "Chapter Prologue",
                datetime.datetime(2023, 11, 25, 0, 0),
            ),
            (
                "https://helscans.com/theatrical-regression-life-chapter-1/",
                "Chapter 1",
                datetime.datetime(2023, 11, 25, 0, 0),
            ),
            (
                "https://helscans.com/theatrical-regression-life-chapter-2/",
                "Chapter 2",
                datetime.datetime(2023, 11, 26, 0, 0),
            ),
            (
                "https://helscans.com/theatrical-regression-life-chapter-3/",
                "Chapter 3",
                datetime.datetime(2023, 11, 27, 0, 0),
            ),
            (
                "https://helscans.com/theatrical-regression-life-chapter-4/",
                "Chapter 4",
                datetime.datetime(2023, 11, 27, 0, 0),
            ),
            (
                "https://helscans.com/theatrical-regression-life-chapter-5/",
                "Chapter 5",
                datetime.datetime(2023, 11, 28, 0, 0),
            ),
        ]
        self.assertEqual([(chapter.url, chapter.title, chapter.pub_date) for chapter in actual[:6]], expected)


@pytest.mark.live
class ChapterScraperTestCase(TestCase):
    def test_process_chapter(self):
        chapter = data.Chapter(url=URL2, title="Chapter 2")
        scraper = helscans.ChapterScraper()
        scraper.process_chapter(chapter)

        self.assertIsNotNone(chapter.original_html)
        self.assertNotEqual(chapter.original_html, "")
        self.assertIn("Lee Jaehun was an undeniable villain that no one could refute", chapter.original_html)

        self.assertIsNotNone(chapter.html)
        self.assertNotEqual(chapter.html, "")
        self.assertIn("Lee Jaehun was an undeniable villain that no one could refute", chapter.html)
