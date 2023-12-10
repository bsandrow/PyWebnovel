"""Live tests for PandaTL."""

import datetime
from unittest import TestCase, mock

import pytest

from webnovel import data
from webnovel.sites import pandatl

URL1 = "https://pandatl.com/novel/surviving-as-a-mage-in-a-magic-academy/"
URL2 = "https://pandatl.com/novel/surviving-as-a-mage-in-a-magic-academy/chapter-1/"


@pytest.mark.live
class NovelScraperTestCase(TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # NOTE: doing this here to minimize the number of times we hit the site.
        #       NovelBin is very aggressive in their anti-DDOS measures, so
        #       let's not trigger rate limiting if we don't have to.
        cls.scraper = pandatl.NovelScraper()
        cls.page = cls.scraper.get_page(url=URL1)

    expected_synopsis = (
        '<div class="summary__content show-more">\n'
        '<p class="font_8">\u200bGraduate student Yi-han finds himself reborn in another world as the youngest child of a mage family.</p>\n'
        '<p class="font_8">-I’m never attending school, ever again!</p>\n'
        '<p class="font_8">‘What do you wish to achieve in life?’</p>\n'
        '<p class="font_8">‘I wish to play around and live comforta-‘</p>\n'
        '<p class="font_8">‘You must be aware of your talent. Now go attend Einroguard!’</p>\n'
        '<p class="font_8">‘Patriarch!’</p>\n'
        '<p class="font_8">My future would be guaranteed once I graduate. For my future!</p>\n'
        "</div>"
    )

    def test_get_status_section(self):
        actual = self.scraper.get_status_section(self.page)
        actual_ = {key: value.text.strip() for key, value in actual.items()}
        expected = {
            "Alternative": "마법학교 마법사로 살아가는 법 ; Magic Academy Survival Guide",
            "Rank": mock.ANY,  # this value frequently fluctuates
            "Rating": mock.ANY,  # this value frequently fluctuates
            "Project": "Active",
            "Novel": "OnGoing",
            "Genre(s)": "Comedy, Fantasy, School Life",
            "Team": "Editor: ally,Translator: Cipher",
            "Tag(s)": "Adapted to Manhwa",
            "Author(s)": "글쓰는기계",
            "Type": "Web Novel (Korean)",
        }
        self.assertEqual(actual_, expected)

    def test_get_genres(self):
        actual = self.scraper.get_genres(self.page)
        expected = ["Comedy", "Fantasy", "School Life"]
        self.assertEqual(actual, expected)

    def test_get_tags(self):
        actual = self.scraper.get_tags(self.page)
        expected = ["Adapted to Manhwa"]
        self.assertEqual(actual, expected)

    def test_title(self):
        actual_title = self.scraper.get_title(self.page)
        expected_title = "Surviving as a Mage in a Magic Academy"
        self.assertEqual(actual_title, expected_title)

    def test_status(self):
        actual = self.scraper.get_status(self.page)
        expected = data.NovelStatus.ONGOING
        self.assertEqual(actual, expected)

    def test_get_author(self):
        actual = self.scraper.get_author(self.page)
        expected = data.Person(
            name="글쓰는기계",
            url="https://pandatl.com/novel-author/%ea%b8%80%ec%93%b0%eb%8a%94%ea%b8%b0%ea%b3%84/",
        )
        self.assertEqual(actual, expected)

    def test_summary(self):
        actual = str(self.scraper.get_summary(self.page))
        print(f"{actual!r}")
        self.assertEqual(actual, self.expected_synopsis)

    def test_cover_image(self):
        actual: data.Image = self.scraper.get_cover_image(self.page)
        self.assertEqual(
            actual.url,
            "https://pandatl.com/wp-content/uploads/2023/01/gVEE6IrdSwMbUxgS3VaRew38Efsr3_Mxszsbo1yugJuZwjj169yZNeigUE-xLI7gtO5VBehZM9ensmMmf9VLcklMBdYnrS1yFO3AFLK2hgHU7jAsJ4-h96iL4R6ldRzYY_x1mUpsjbXy-ulw4KoxEw-193x278.webp",
        )
        self.assertIsNone(actual.mimetype)

    def test_novel_id(self):
        actual = self.scraper.get_novel_id(url=URL1)
        expected = "surviving-as-a-mage-in-a-magic-academy"
        self.assertEqual(actual, expected)

    def test_chapters(self):
        actual = self.scraper.get_chapters(page=self.page, url=URL1)
        expected = [
            (
                "https://pandatl.com/novel/surviving-as-a-mage-in-a-magic-academy/chapter-1/",
                "Chapter 1",
                datetime.datetime(2023, 1, 21, 0, 0),
            ),
            (
                "https://pandatl.com/novel/surviving-as-a-mage-in-a-magic-academy/chapter-2/",
                "Chapter 2",
                datetime.datetime(2023, 1, 21, 0, 0),
            ),
            (
                "https://pandatl.com/novel/surviving-as-a-mage-in-a-magic-academy/chapter-3/",
                "Chapter 3",
                datetime.datetime(2023, 1, 21, 0, 0),
            ),
            (
                "https://pandatl.com/novel/surviving-as-a-mage-in-a-magic-academy/chapter-4/",
                "Chapter 4",
                datetime.datetime(2023, 1, 21, 0, 0),
            ),
            (
                "https://pandatl.com/novel/surviving-as-a-mage-in-a-magic-academy/chapter-5/",
                "Chapter 5",
                datetime.datetime(2023, 1, 21, 0, 0),
            ),
            (
                "https://pandatl.com/novel/surviving-as-a-mage-in-a-magic-academy/chapter-6/",
                "Chapter 6",
                datetime.datetime(2023, 1, 21, 0, 0),
            ),
        ]
        self.assertEqual([(chapter.url, chapter.title, chapter.pub_date) for chapter in actual[:6]], expected)


@pytest.mark.live
class ChapterScraperTestCase(TestCase):
    def test_process_chapter(self):
        chapter = data.Chapter(url=URL2, title="Chapter 2")
        scraper = pandatl.ChapterScraper()
        scraper.process_chapter(chapter)

        # Make sure that we don't end up with nothing
        self.assertIsNotNone(chapter.original_html)
        self.assertIsNotNone(chapter.html)
        self.assertNotEqual(chapter.original_html, "")
        self.assertNotEqual(chapter.html, "")

        # Check if a known block of text that should be there exists in the
        # content.
        self.assertIn(
            "I’m never attending school, ever again. From now on, I’ll live life for myself!", chapter.original_html
        )
        self.assertIn("I’m never attending school, ever again. From now on, I’ll live life for myself!", chapter.html)

        self.assertIn(
            "A boy who was dressed the most extravagantly among all the new students was waving at him.",
            chapter.original_html,
        )
        self.assertIn(
            "A boy who was dressed the most extravagantly among all the new students was waving at him.", chapter.html
        )
