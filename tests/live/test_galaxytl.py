"""Live tests for GalaxyTL."""

import datetime
from unittest import TestCase, mock

import pytest

from webnovel import data
from webnovel.sites import galaxytl

URL1 = "https://galaxytranslations97.com/novel/the-knight-king-who-returned-with-a-god/"
URL2 = "https://galaxytranslations97.com/novel/the-knight-king-who-returned-with-a-god/chapter-1/"


@pytest.mark.live
class NovelScraperTestCase(TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # NOTE: doing this here to minimize the number of times we hit the site.
        #       NovelBin is very aggressive in their anti-DDOS measures, so
        #       let's not trigger rate limiting if we don't have to.
        cls.scraper = galaxytl.NovelScraper()
        cls.page = cls.scraper.get_page(url=URL1)

    expected_synopsis = (
        '<div class="summary__content show-more">\n\n\n'
        "<p>I returned to Earth after hunting demons in the otherworld for three hundred years. But I did not return alone.</p>\n"
        "<!-- AI CONTENT END 2 -->\n"
        "</div>"
    )

    def test_get_status_section(self):
        actual = self.scraper.get_status_section(self.page)
        actual_ = {key: value.text.strip() for key, value in actual.items()}
        expected = {
            "Alternative": "신과함께 돌아온 기사왕님",
            "Rank": mock.ANY,  # this value frequently fluctuates
            "Release": "2022",
            "Status": "OnGoing",
            "Genre(s)": "Korean Novel",
            "Author(s)": "사람살려",
            "Artist(s)": "GalaxyTL",
        }
        self.assertEqual(actual_, expected)

    def test_get_genres(self):
        actual = self.scraper.get_genres(self.page)
        expected = ["Korean Novel"]
        self.assertEqual(actual, expected)

    def test_get_tags(self):
        actual = self.scraper.get_tags(self.page)
        expected = None
        self.assertEqual(actual, expected)

    def test_title(self):
        actual_title = self.scraper.get_title(self.page)
        expected_title = "The Knight King Who Returned With a God"
        self.assertEqual(actual_title, expected_title)

    def test_status(self):
        actual = self.scraper.get_status(self.page)
        expected = data.NovelStatus.ONGOING
        self.assertEqual(actual, expected)

    def test_get_author(self):
        actual = self.scraper.get_author(self.page)
        expected = data.Person(
            name="사람살려", url="https://galaxytranslations97.com/novel-author/%ec%82%ac%eb%9e%8c%ec%82%b4%eb%a0%a4/"
        )
        self.assertEqual(actual, expected)

    def test_summary(self):
        actual = str(self.scraper.get_summary(self.page))
        self.assertEqual(actual, self.expected_synopsis)

    def test_cover_image(self):
        actual: data.Image = self.scraper.get_cover_image(self.page)
        self.assertEqual(
            actual.url,
            "https://i0.wp.com/galaxytranslations97.com/wp-content/uploads/2023/05/6398a9d0e11a5_Xz4F8WGx_c200a322a2ebaca282d4989bfd5b9d79ae28494c.jpg?fit=178%2C278&ssl=1",
        )
        self.assertIsNone(actual.mimetype)

    def test_novel_id(self):
        actual = self.scraper.get_novel_id(url=URL1)
        expected = "the-knight-king-who-returned-with-a-god"
        self.assertEqual(actual, expected)

    def test_chapters(self):
        actual = self.scraper.get_chapters(page=self.page, url=URL1)
        expected = [
            (
                "https://galaxytranslations97.com/novel/the-knight-king-who-returned-with-a-god/chapter-1/",
                "Chapter 1",
                datetime.datetime(2023, 6, 4, 0, 0),
            ),
            (
                "https://galaxytranslations97.com/novel/the-knight-king-who-returned-with-a-god/chapter-2/",
                "Chapter 2",
                datetime.datetime(2023, 6, 4, 0, 0),
            ),
            (
                "https://galaxytranslations97.com/novel/the-knight-king-who-returned-with-a-god/chapter-3/",
                "Chapter 3",
                datetime.datetime(2023, 6, 4, 0, 0),
            ),
            (
                "https://galaxytranslations97.com/novel/the-knight-king-who-returned-with-a-god/chapter-4/",
                "Chapter 4",
                datetime.datetime(2023, 6, 4, 0, 0),
            ),
            (
                "https://galaxytranslations97.com/novel/the-knight-king-who-returned-with-a-god/chapter-5/",
                "Chapter 5",
                datetime.datetime(2023, 6, 4, 0, 0),
            ),
            (
                "https://galaxytranslations97.com/novel/the-knight-king-who-returned-with-a-god/chapter-6/",
                "Chapter 6",
                datetime.datetime(2023, 6, 4, 0, 0),
            ),
        ]
        self.assertEqual([(chapter.url, chapter.title, chapter.pub_date) for chapter in actual[:6]], expected)


@pytest.mark.live
class ChapterScraperTestCase(TestCase):
    def test_process_chapter(self):
        chapter = data.Chapter(url=URL2, title="Chapter 2")
        scraper = galaxytl.ChapterScraper()
        scraper.process_chapter(chapter)

        # Make sure that we don't end up with nothing
        self.assertIsNotNone(chapter.original_html)
        self.assertIsNotNone(chapter.html)
        self.assertNotEqual(chapter.original_html, "")
        self.assertNotEqual(chapter.html, "")

        # Check if a known block of text that should be there exists in the
        # content.
        self.assertIn("~Year 8~", chapter.original_html)
        self.assertIn("~Year 8~", chapter.html)

        self.assertIn("“Ha…….”", chapter.original_html)
        self.assertIn("“Ha…….”", chapter.html)

        self.assertIn("-Demon Lord (Lord of Chaos is the title of a lord)", chapter.original_html)
        self.assertIn("-Demon Lord (Lord of Chaos is the title of a lord)", chapter.html)
