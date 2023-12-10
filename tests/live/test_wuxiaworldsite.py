"""Live tests for WuxiaWorld.site."""

import datetime
from unittest import TestCase, mock

import pytest

from webnovel import data
from webnovel.sites import wuxiaworld_site

URL1 = "https://wuxiaworld.site/novel/global-game-afk-in-the-zombie-apocalypse-game-wuxia-dao-novel/"
URL2 = "https://wuxiaworld.site/novel/global-game-afk-in-the-zombie-apocalypse-game-wuxia-dao-novel/chapter-1/"


@pytest.mark.live
class NovelScraperTestCase(TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # NOTE: doing this here to minimize the number of times we hit the site.
        #       NovelBin is very aggressive in their anti-DDOS measures, so
        #       let's not trigger rate limiting if we don't have to.
        cls.scraper = wuxiaworld_site.NovelScraper()
        cls.page = cls.scraper.get_page(url=URL1)

    expected_synopsis = (
        '<div class="summary__content show-more">\n'
        "<p><b><em>You’re Reading “Global Game: AFK In The Zombie Apocalypse Game”"
        " on WuxiaWorld.Site</em></b><br/>\nFang Heng was transmigrated to a "
        "parallel world and his soul was forced into the body of a man who had "
        "just committed suicide.<br/>\nHuh? What? Every human here was being forced "
        "to join a game? Those who refused would be killed?<br/>\nWait? This suicide "
        "dude was a pro gamer?<br/>\nHe had the highest S-rank talent sill, the "
        "Zombie Clone?<br/>\nDamn! The S-rank skill evolved! My zombie clones "
        "could auto hunt!<br/>\n[Your zombie army has crafted Wooden Axe x720 "
        "when you were offline. You have received 1921 experience points for "
        "the Basic Crafting skill.]<br/>\n[Your zombie army has chopped down "
        "27,821 trees and gathered 128,973 pieces of wood while you were "
        "offline. You have received 2,171,921 experience points for the Basic "
        "Wood Chopping skill.]<br/>\nJust as the rest of the players were "
        "struggling to survive in the zombie apocalyptic game, Fang Heng’s "
        "zombie clones were starting to clear every resource out of the forest."
        "<br/>\nHm… What an interesting game!</p>\n</div>"
    )

    def test_get_status_section(self):
        actual = self.scraper.get_status_section(self.page)
        actual_ = {key: value.text.strip() for key, value in actual.items()}
        expected = {
            "Rank": mock.ANY,  # this value frequently fluctuates
            "Rating": mock.ANY,  # this value frequently fluctuates
            "Release": "2021",
            "Status": "OnGoing",
            "Genre(s)": "Video Games",
            "Author(s)": "Empire Black Knight",
            "Type": "Web Novel (CN)",
        }
        self.assertEqual(actual_, expected)

    def test_get_genres(self):
        actual = self.scraper.get_genres(self.page)
        expected = ["Video Games"]
        self.assertEqual(actual, expected)

    def test_get_tags(self):
        actual = self.scraper.get_tags(self.page)
        expected = None
        self.assertEqual(actual, expected)

    def test_title(self):
        actual_title = self.scraper.get_title(self.page)
        expected_title = "Global Game: AFK In The Zombie Apocalypse Game"
        self.assertEqual(actual_title, expected_title)

    def test_status(self):
        actual = self.scraper.get_status(self.page)
        expected = data.NovelStatus.ONGOING
        self.assertEqual(actual, expected)

    def test_get_author(self):
        actual = self.scraper.get_author(self.page)
        expected = data.Person(
            name="Empire Black Knight",
            url="https://wuxiaworld.site/manga-author/empire-black-knight/",
        )
        self.assertEqual(actual, expected)

    def test_summary(self):
        actual = str(self.scraper.get_summary(self.page))
        self.assertEqual(actual, self.expected_synopsis)

    def test_cover_image(self):
        actual: data.Image = self.scraper.get_cover_image(self.page)
        self.assertEqual(
            actual.url,
            "https://wuxiaworld.site/wp-content/uploads/2022/01/thumb_61e1160221cc0-193x278.jpgrender_jsfalse",
        )
        self.assertIsNone(actual.mimetype)

    def test_novel_id(self):
        actual = self.scraper.get_novel_id(url=URL1)
        expected = "global-game-afk-in-the-zombie-apocalypse-game-wuxia-dao-novel"
        self.assertEqual(actual, expected)

    def test_chapters(self):
        actual = self.scraper.get_chapters(page=self.page, url=URL1)
        expected = [
            (
                "https://wuxiaworld.site/novel/global-game-afk-in-the-zombie-apocalypse-game-wuxia-dao-novel/chapter-1/",
                "Chapter 1",
                datetime.datetime(2022, 1, 14, 0, 0),
            ),
            (
                "https://wuxiaworld.site/novel/global-game-afk-in-the-zombie-apocalypse-game-wuxia-dao-novel/chapter-2/",
                "Chapter 2",
                datetime.datetime(2022, 1, 14, 0, 0),
            ),
            (
                "https://wuxiaworld.site/novel/global-game-afk-in-the-zombie-apocalypse-game-wuxia-dao-novel/chapter-3/",
                "Chapter 3",
                datetime.datetime(2022, 1, 14, 0, 0),
            ),
            (
                "https://wuxiaworld.site/novel/global-game-afk-in-the-zombie-apocalypse-game-wuxia-dao-novel/chapter-4/",
                "Chapter 4",
                datetime.datetime(2022, 1, 14, 0, 0),
            ),
            (
                "https://wuxiaworld.site/novel/global-game-afk-in-the-zombie-apocalypse-game-wuxia-dao-novel/chapter-5/",
                "Chapter 5",
                datetime.datetime(2022, 1, 14, 0, 0),
            ),
            (
                "https://wuxiaworld.site/novel/global-game-afk-in-the-zombie-apocalypse-game-wuxia-dao-novel/chapter-6/",
                "Chapter 6",
                datetime.datetime(2022, 1, 14, 0, 0),
            ),
        ]
        self.assertEqual([(chapter.url, chapter.title, chapter.pub_date) for chapter in actual[:6]], expected)


@pytest.mark.live
class ChapterScraperTestCase(TestCase):
    def test_process_chapter(self):
        chapter = data.Chapter(url=URL2, title="Chapter 2")
        scraper = wuxiaworld_site.ChapterScraper()
        scraper.process_chapter(chapter)

        # Make sure that we don't end up with nothing
        self.assertIsNotNone(chapter.original_html)
        self.assertIsNotNone(chapter.html)
        self.assertNotEqual(chapter.original_html, "")
        self.assertNotEqual(chapter.html, "")

        # Check if a known block of text that should be there exists in the
        # content.
        self.assertIn(
            "Early June, the weather was hot and humid, and it was drizzling outside the window", chapter.original_html
        )
        self.assertIn(
            "Early June, the weather was hot and humid, and it was drizzling outside the window", chapter.html
        )

        self.assertIn("[2: Upgrade your talent.]", chapter.original_html)
        self.assertIn("[2: Upgrade your talent.]", chapter.html)
