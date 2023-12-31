import datetime
from unittest import TestCase

from bs4 import BeautifulSoup

from webnovel import errors
from webnovel.data import Chapter, Image, NovelStatus, Person
from webnovel.html import remove_element
from webnovel.sites import novelcool

from ..helpers import get_test_data

NOVEL_PAGE = get_test_data("novelcool/novel.html")
CHAPTER_PAGE = get_test_data("novelcool/chapter.html")


class NovelCoolScraperTestCase(TestCase):
    maxDiff = None

    def test_get_novel_id(self):
        self.assertEqual(
            novelcool.NovelCoolScraper.get_novel_id("https://www.novelcool.com/novel/Creepy-Story-Club.html"),
            "Creepy-Story-Club",
        )

    def test_supports_url(self):
        self.assertTrue(novelcool.NovelCoolScraper.supports_url("https://novelcool.com/novel/Creepy-Story-Club.html"))
        self.assertTrue(novelcool.NovelCoolScraper.supports_url("http://novelcool.com/novel/Creepy-Story-Club.html"))
        self.assertTrue(
            novelcool.NovelCoolScraper.supports_url("http://www.novelcool.com/novel/Creepy-Story-Club.html")
        )
        self.assertFalse(novelcool.NovelCoolScraper.supports_url("http://www.novelcool.com/novel/Creepy-Story-Club"))

    def test_get_title(self):
        page = BeautifulSoup(NOVEL_PAGE, "html.parser")
        actual = novelcool.NovelCoolScraper().get_title(page)
        expected = "Creepy Story Club"
        self.assertEqual(actual, expected)

    def test_get_author(self):
        page = BeautifulSoup(NOVEL_PAGE, "html.parser")
        actual = novelcool.NovelCoolScraper().get_author(page)
        expected = Person(name="每月一更")
        self.assertEqual(actual, expected)

    def test_get_status(self):
        page = BeautifulSoup(NOVEL_PAGE, "html.parser")
        actual = novelcool.NovelCoolScraper().get_status(page)
        expected = NovelStatus.ONGOING
        self.assertEqual(actual, expected)

    def test_get_cover_image(self):
        page = BeautifulSoup(NOVEL_PAGE, "html.parser")
        actual = novelcool.NovelCoolScraper().get_cover_image(page)
        expected = Image(url="https://img.novelcool.com/logo/202207/ae/creepy_story_club3051.jpg")
        self.assertEqual(actual, expected)

    def test_get_genres(self):
        page = BeautifulSoup(NOVEL_PAGE, "html.parser")
        actual = set(novelcool.NovelCoolScraper().get_genres(page))
        expected = {"Fantasy", "Creepy", "Xuanhuan"}
        self.assertEqual(actual, expected)

    def test_get_summary(self):
        page = BeautifulSoup(NOVEL_PAGE, "html.parser")
        actual = novelcool.NovelCoolScraper().get_summary(page)
        expected = (
            "Left out during elementary school picnic.\n"
            "    Left out during middle school camp.\n"
            "    Left out during high school trip.\n"
            "    I finally became a college student and what? I'm left out from the entire humanity?\n"
            "    Yu Ilhan who protects earth alone while everybody's away on other worlds.\n"
            "    His legend starts after humanity comes back and meets the Great Cataclysm!"
        )
        self.assertEqual(actual, expected)

    def test_get_chapters(self):
        page = BeautifulSoup(NOVEL_PAGE, "html.parser")
        actual = novelcool.NovelCoolScraper().get_chapters(page, url="")
        expected = list(
            reversed(
                [
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-32/8530107/",
                        title="Creepy Story Club Chapter 32",
                        chapter_no=32,
                        slug="creepy-story-club-Chapter-32",
                        html=None,
                        pub_date=datetime.date(2022, 8, 20),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-31/8530106/",
                        title="Creepy Story Club Chapter 31",
                        chapter_no=31,
                        slug="creepy-story-club-Chapter-31",
                        html=None,
                        pub_date=datetime.date(2022, 8, 20),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-30/8530105/",
                        title="Creepy Story Club Chapter 30",
                        chapter_no=30,
                        slug="creepy-story-club-Chapter-30",
                        html=None,
                        pub_date=datetime.date(2022, 8, 20),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-29/8530104/",
                        title="Creepy Story Club Chapter 29",
                        chapter_no=29,
                        slug="creepy-story-club-Chapter-29",
                        html=None,
                        pub_date=datetime.date(2022, 8, 20),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-28/8530103/",
                        title="Creepy Story Club Chapter 28",
                        chapter_no=28,
                        slug="creepy-story-club-Chapter-28",
                        html=None,
                        pub_date=datetime.date(2022, 8, 20),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-27/8530102/",
                        title="Creepy Story Club Chapter 27",
                        chapter_no=27,
                        slug="creepy-story-club-Chapter-27",
                        html=None,
                        pub_date=datetime.date(2022, 8, 20),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-26/8530101/",
                        title="Creepy Story Club Chapter 26",
                        chapter_no=26,
                        slug="creepy-story-club-Chapter-26",
                        html=None,
                        pub_date=datetime.date(2022, 8, 20),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-25/8530100/",
                        title="Creepy Story Club Chapter 25",
                        chapter_no=25,
                        slug="creepy-story-club-Chapter-25",
                        html=None,
                        pub_date=datetime.date(2022, 8, 20),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-24/8530099/",
                        title="Creepy Story Club Chapter 24",
                        chapter_no=24,
                        slug="creepy-story-club-Chapter-24",
                        html=None,
                        pub_date=datetime.date(2022, 8, 20),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-23/8530098/",
                        title="Creepy Story Club Chapter 23",
                        chapter_no=23,
                        slug="creepy-story-club-Chapter-23",
                        html=None,
                        pub_date=datetime.date(2022, 8, 20),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-22/8530097/",
                        title="Creepy Story Club Chapter 22",
                        chapter_no=22,
                        slug="creepy-story-club-Chapter-22",
                        html=None,
                        pub_date=datetime.date(2022, 8, 20),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-21/8530096/",
                        title="Creepy Story Club Chapter 21",
                        chapter_no=21,
                        slug="creepy-story-club-Chapter-21",
                        html=None,
                        pub_date=datetime.date(2022, 8, 20),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-20/8530095/",
                        title="Creepy Story Club Chapter 20",
                        chapter_no=20,
                        slug="creepy-story-club-Chapter-20",
                        html=None,
                        pub_date=datetime.date(2022, 8, 20),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-19/8530094/",
                        title="Creepy Story Club Chapter 19",
                        chapter_no=19,
                        slug="creepy-story-club-Chapter-19",
                        html=None,
                        pub_date=datetime.date(2022, 8, 20),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-18/8411284/",
                        title="Creepy Story Club Chapter 18",
                        chapter_no=18,
                        slug="creepy-story-club-Chapter-18",
                        html=None,
                        pub_date=datetime.date(2022, 8, 5),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-17/8411283/",
                        title="Creepy Story Club Chapter 17",
                        chapter_no=17,
                        slug="creepy-story-club-Chapter-17",
                        html=None,
                        pub_date=datetime.date(2022, 8, 5),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-16/8411282/",
                        title="Creepy Story Club Chapter 16",
                        chapter_no=16,
                        slug="creepy-story-club-Chapter-16",
                        html=None,
                        pub_date=datetime.date(2022, 8, 5),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-15/8411281/",
                        title="Creepy Story Club Chapter 15",
                        chapter_no=15,
                        slug="creepy-story-club-Chapter-15",
                        html=None,
                        pub_date=datetime.date(2022, 8, 5),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-14/8411280/",
                        title="Creepy Story Club Chapter 14",
                        chapter_no=14,
                        slug="creepy-story-club-Chapter-14",
                        html=None,
                        pub_date=datetime.date(2022, 8, 5),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-13/8411279/",
                        title="Creepy Story Club Chapter 13",
                        chapter_no=13,
                        slug="creepy-story-club-Chapter-13",
                        html=None,
                        pub_date=datetime.date(2022, 8, 5),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-12/8411278/",
                        title="Creepy Story Club Chapter 12",
                        chapter_no=12,
                        slug="creepy-story-club-Chapter-12",
                        html=None,
                        pub_date=datetime.date(2022, 8, 5),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-11/8411277/",
                        title="Creepy Story Club Chapter 11",
                        chapter_no=11,
                        slug="creepy-story-club-Chapter-11",
                        html=None,
                        pub_date=datetime.date(2022, 8, 5),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-10/8411276/",
                        title="Creepy Story Club Chapter 10",
                        chapter_no=10,
                        slug="creepy-story-club-Chapter-10",
                        html=None,
                        pub_date=datetime.date(2022, 8, 5),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-9/8306193/",
                        title="Creepy Story Club Chapter 9",
                        chapter_no=9,
                        slug="creepy-story-club-Chapter-9",
                        html=None,
                        pub_date=datetime.date(2022, 7, 26),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-8/8306190/",
                        title="Creepy Story Club Chapter 8",
                        chapter_no=8,
                        slug="creepy-story-club-Chapter-8",
                        html=None,
                        pub_date=datetime.date(2022, 7, 26),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-7/8306187/",
                        title="Creepy Story Club Chapter 7",
                        chapter_no=7,
                        slug="creepy-story-club-Chapter-7",
                        html=None,
                        pub_date=datetime.date(2022, 7, 26),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-6/8262479/",
                        title="Creepy Story Club Chapter 6",
                        chapter_no=6,
                        slug="creepy-story-club-Chapter-6",
                        html=None,
                        pub_date=datetime.date(2022, 7, 23),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-5/8262478/",
                        title="Creepy Story Club Chapter 5",
                        chapter_no=5,
                        slug="creepy-story-club-Chapter-5",
                        html=None,
                        pub_date=datetime.date(2022, 7, 23),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-4/8262477/",
                        title="Creepy Story Club Chapter 4",
                        chapter_no=4,
                        slug="creepy-story-club-Chapter-4",
                        html=None,
                        pub_date=datetime.date(2022, 7, 23),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-3/8262476/",
                        title="Creepy Story Club Chapter 3",
                        chapter_no=3,
                        slug="creepy-story-club-Chapter-3",
                        html=None,
                        pub_date=datetime.date(2022, 7, 23),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-2/8262475/",
                        title="Creepy Story Club Chapter 2",
                        chapter_no=2,
                        slug="creepy-story-club-Chapter-2",
                        html=None,
                        pub_date=datetime.date(2022, 7, 23),
                    ),
                    Chapter(
                        url="https://www.novelcool.com/chapter/creepy-story-club-Chapter-1/8262474/",
                        title="Creepy Story Club Chapter 1",
                        chapter_no=1,
                        slug="creepy-story-club-Chapter-1",
                        html=None,
                        pub_date=datetime.date(2022, 7, 23),
                    ),
                ]
            )
        )
        self.assertEqual(actual, expected)


class NovelCoolChapterScraperTestCase(TestCase):
    maxDiff = None

    def test_get_content(self):
        page = BeautifulSoup(CHAPTER_PAGE, "html.parser")
        actual = novelcool.NovelCoolChapterScraper().get_content(page)
        expected = page.select_one(".overflow-hidden")
        self.assertEqual(actual, expected)

    def test_get_content_with_no_start_end_marks(self):
        page = BeautifulSoup(CHAPTER_PAGE, "html.parser")
        remove_element(page.select_one(".chapter-start-mark"))
        remove_element(page.select_one(".chapter-end-mark"))

        with self.assertRaisesRegex(
            errors.ChapterContentNotFound, r"Unable to find \.chapter-start-mark / \.chapter-end-mark"
        ):
            novelcool.NovelCoolChapterScraper().get_content(page)

    def test_get_content_with_post_processing(self):
        page = BeautifulSoup(CHAPTER_PAGE, "html.parser")
        chapter = Chapter(
            url="https://example.com",
            title="Chapter 32",
            original_html=str(novelcool.NovelCoolChapterScraper().get_content(page)),
            filters=novelcool.NovelCoolChapterScraper.content_filters,
        )
        novelcool.NovelCoolChapterScraper().post_processing(chapter)
        expected = (
            '<div class="overflow-hidden">\n\n'
            "\n\n\n"
            "<p>Chapter 32 — Lorem Ipsum Loren Ipsum! Lorem of the Ipsum</p>\n"
            "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>\n"
            "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>\n"
            "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>\n"
            "\n\n"
            "</div>"
        )
        self.assertEqual(chapter.html, expected)
