"""Live tests for NovelBin.net."""

import datetime
from unittest import TestCase

import pytest

from webnovel import data
from webnovel.sites import novelbin

URL1 = "https://novelbin.net/n/my-vampire-system-nov-1050389520"
URL2 = "https://novelbin.net/n/my-vampire-system-nov-1050389520/chapter-6"


@pytest.mark.live
class NovelScraperTestCase(TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # NOTE: doing this here to minimize the number of times we hit the site.
        #       NovelBin is very aggressive in their anti-DDOS measures, so
        #       let's not trigger rate limiting if we don't have to.
        cls.scraper = novelbin.NovelScraper()
        cls.page = cls.scraper.get_page(url=URL1)

    expected_synopsis = (
        '<div class="desc-text" itemprop="description">\n'
        "The human Race is at war with the Vicious Dalki and when they needed "
        "help more than ever, THEY started to come forward.\nHumans who had "
        "hidden in the shadows for hundreds of years, people with abilities.\n"
        "Some chose to share their knowledge to the rest of the world in hopes of "
        "winning the war, while others kept their abilities to themselves.\n"
        "Quinn had lost everything to the war, his home, his family and the only "
        "thing he had inherited was a crummy old book that he couldn’t even "
        "open.\nBut when the book had finally opened, Quinn was granted a system "
        "and his whole life was turned around.\nHe completed quest after quest "
        "and became more powerful, until one day the system gave him a quest he "
        "wasn’t sure he could complete.\n“It is time to feed!”\n“You must drink "
        "human blood within 24 hours”\n“Your HP will continue to decrease until "
        "the task has been completed”\n"
        "</div>"
    )

    def test_title(self):
        actual_title = self.scraper.get_title(self.page)
        expected_title = "My Vampire System"
        self.assertEqual(actual_title, expected_title)

    def test_status(self):
        actual = self.scraper.get_status(self.page)
        expected = data.NovelStatus.ONGOING
        self.assertEqual(actual, expected)

    def test_genres(self):
        actual_genres = self.scraper.get_genres(self.page)
        expected_genres = ["Action", "Fantasy", "Mystery"]
        self.assertEqual(actual_genres, expected_genres)

    def test_author(self):
        actual = self.scraper.get_author(self.page)
        expected = data.Person(name="Jksmanga", email=None, url="https://novelbin.net/a/Jksmanga")
        self.assertEqual(actual, expected)

    def test_summary(self):
        actual = str(self.scraper.get_summary(self.page))
        self.assertEqual(actual, self.expected_synopsis)

    def test_cover_image(self):
        actual: data.Image = self.scraper.get_cover_image(self.page)
        self.assertEqual(actual.url, "https://novelbin.net/media/novel/my-vampire-system.jpg")
        self.assertIsNone(actual.mimetype)

    def test_novel_id(self):
        scraper = novelbin.NovelScraper()
        actual = scraper.get_novel_id(url=URL1)
        expected = "my-vampire-system"
        self.assertEqual(actual, expected)

    def test_chapters(self):
        actual = self.scraper.get_chapters(page=self.page, url=URL1)
        expected = [
            (
                "https://novelbin.net/n/my-vampire-system-nov-1050389520/chapter-1",
                "Chapter 1: Just an old Book",
                None,
            ),
            (
                "https://novelbin.net/n/my-vampire-system-nov-1050389520/chapter-2",
                "Chapter 2: Daily Ques",
                None,
            ),
            (
                "https://novelbin.net/n/my-vampire-system-nov-1050389520/chapter-3",
                "Chapter 3: Miltary School",
                None,
            ),
            (
                "https://novelbin.net/n/my-vampire-system-nov-1050389520/chapter-4",
                "Chapter 4: Ability Level",
                None,
            ),
            (
                "https://novelbin.net/n/my-vampire-system-nov-1050389520/chapter-5",
                "Chapter 5: No Ability",
                None,
            ),
            (
                "https://novelbin.net/n/my-vampire-system-nov-1050389520/chapter-6",
                "Chapter 6: Resul",
                None,
            ),
        ]
        self.assertEqual([(chapter.url, chapter.title, chapter.pub_date) for chapter in actual[:6]], expected)
        self.assertTrue(len(actual) >= 2545)


@pytest.mark.live
class ChapterScraperTestCase(TestCase):
    def test_process_chapter(self):
        chapter = data.Chapter(url=URL2, title="Chapter 6: Resul")
        scraper = novelbin.ChapterScraper()
        scraper.process_chapter(chapter)

        # Make sure that we don't end up with nothing
        self.assertIsNotNone(chapter.original_html)
        self.assertIsNotNone(chapter.html)
        self.assertNotEqual(chapter.original_html, "")
        self.assertNotEqual(chapter.html, "")

        # Check if a known block of text that should be there exists in the
        # content.
        self.assertIn("Quinn thought the whole thing was ridiculous", chapter.original_html)
        self.assertIn("Quinn thought the whole thing was ridiculous", chapter.html)

        self.assertIn("Quinn thought the whole thing was a joke", chapter.original_html)
        self.assertIn("Quinn thought the whole thing was a joke", chapter.html)
