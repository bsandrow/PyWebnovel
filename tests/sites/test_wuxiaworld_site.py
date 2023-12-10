from unittest import TestCase, mock, skip

import requests_mock

from webnovel.data import Chapter, Image, Novel, NovelStatus, Person
from webnovel.sites import wuxiaworld_site

from ..helpers import get_test_data


@skip
class WuxiaWorldSiteTestCase(TestCase):
    def test_supports_url(self):
        for url, expected_result in [
            ("https://wuxiaworld.site/novel/global-game-afk-in-the-zombie-apocalypse-game-wuxia-dao-novel/", True),
            ("https://www.wuxiaworld.site/novel/global-game-afk-in-the-zombie-apocalypse-game-wuxia-dao-novel/", True),
            ("http://wuxiaworld.site/novel/global-game-afk-in-the-zombie-apocalypse-game-wuxia-dao-novel/", True),
            ("http://wuxiaworld.site/novel/global-game-afk-in-the-zombie-apocalypse-game-wuxia-dao-novel", False),
        ]:
            with self.subTest(url=url, expected_result=expected_result):
                actual_result = wuxiaworld_site.supports_url(url)
                self.assertTrue(actual_result is expected_result)


@skip
class WuxiaWorldDotSiteScraperTestCase(TestCase):
    novel_page: str
    chlist_page: str

    @classmethod
    def setUpClass(cls):
        cls.novel_page = get_test_data("wuxiaworldsite/novel.html")
        cls.chlist_page = get_test_data("wuxiaworldsite/chlist.html")

    def setUp(self):
        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        self.requests_mock.get(
            "/novel/global-game-afk-in-the-zombie-apocalypse-game-wuxia-dao-novel/", text=self.novel_page
        )
        self.requests_mock.post(
            "/novel/global-game-afk-in-the-zombie-apocalypse-game-wuxia-dao-novel/ajax/chapters/", text=self.chlist_page
        )

    def tearDown(self):
        self.requests_mock.stop()

    def test_get_title(self):
        scraper = wuxiaworld_site.NovelScraper()
        soup = scraper.get_soup(self.novel_page)
        self.assertEqual(scraper.get_title(soup), "Global Game: AFK In The Zombie Apocalypse Game")

    def test_get_status(self):
        scraper = wuxiaworld_site.NovelScraper()
        soup = scraper.get_soup(self.novel_page)
        self.assertEqual(scraper.get_status(soup), NovelStatus.ONGOING)

    def test_get_genres(self):
        scraper = wuxiaworld_site.NovelScraper()
        soup = scraper.get_soup(self.novel_page)
        self.assertEqual(scraper.get_genres(soup), ["Video Games"])

    def test_get_author(self):
        scraper = wuxiaworld_site.NovelScraper()
        soup = scraper.get_soup(self.novel_page)
        self.assertEqual(
            scraper.get_author(soup),
            Person(name="Empire Black Knight", url="https://wuxiaworld.site/manga-author/empire-black-knight/"),
        )

    def test_get_cover_image(self):
        scraper = wuxiaworld_site.NovelScraper()
        soup = scraper.get_soup(self.novel_page)
        self.assertEqual(
            scraper.get_cover_image(soup),
            Image(
                url="https://wuxiaworld.site/wp-content/uploads/2022/01/thumb_61e1160221cc0-193x278.jpgrender_jsfalse"
            ),
        )

    def test_get_summary(self):
        self.maxDiff = None
        scraper = wuxiaworld_site.NovelScraper()
        soup = scraper.get_soup(self.novel_page)
        self.assertEqual(
            scraper.get_summary(soup),
            (
                "You’re Reading “Global Game: AFK In The Zombie Apocalypse Game” on WuxiaWorld.Site\n"
                "Fang Heng was transmigrated to a parallel world and his soul was forced into the body of a man who had"
                " just committed suicide.\n"
                "Huh? What? Every human here was being forced to join a game? Those who refused would be killed?\n"
                "Wait? This suicide dude was a pro gamer?\n"
                "He had the highest S-rank talent sill, the Zombie Clone?\n"
                "Damn! The S-rank skill evolved! My zombie clones could auto hunt!\n"
                "[Your zombie army has crafted Wooden Axe x720 when you were offline. You have received 1921 experience"
                " points for the Basic Crafting skill.]\n"
                "[Your zombie army has chopped down 27,821 trees and gathered 128,973 pieces of wood while you were "
                "offline. You have received 2,171,921 experience points for the Basic Wood Chopping skill.]\n"
                "Just as the rest of the players were struggling to survive in the zombie apocalyptic game, Fang Heng’s"
                " zombie clones were starting to clear every resource out of the forest.\n"
                "Hm… What an interesting game!"
            ),
        )

    def test_scrape(self):
        url = "https://wuxiaworld.site/novel/global-game-afk-in-the-zombie-apocalypse-game-wuxia-dao-novel/"
        scraper = wuxiaworld_site.NovelScraper()
        novel = scraper.scrape(url)

        expected_novel = Novel(
            url="https://wuxiaworld.site/novel/global-game-afk-in-the-zombie-apocalypse-game-wuxia-dao-novel/",
            title="Global Game: AFK In The Zombie Apocalypse Game",
            status=NovelStatus.ONGOING,
            genres=["Video Games"],
            author=Person(name="Empire Black Knight", url="https://wuxiaworld.site/manga-author/empire-black-knight/"),
            cover_image=Image(
                url="https://wuxiaworld.site/wp-content/uploads/2022/01/thumb_61e1160221cc0-193x278.jpgrender_jsfalse"
            ),
            summary=(
                "You’re Reading “Global Game: AFK In The Zombie Apocalypse Game” on WuxiaWorld.Site\n"
                "Fang Heng was transmigrated to a parallel world and his soul was forced into the body of a man who had"
                " just committed suicide.\n"
                "Huh? What? Every human here was being forced to join a game? Those who refused would be killed?\n"
                "Wait? This suicide dude was a pro gamer?\n"
                "He had the highest S-rank talent sill, the Zombie Clone?\n"
                "Damn! The S-rank skill evolved! My zombie clones could auto hunt!\n"
                "[Your zombie army has crafted Wooden Axe x720 when you were offline. You have received 1921 experience"
                " points for the Basic Crafting skill.]\n"
                "[Your zombie army has chopped down 27,821 trees and gathered 128,973 pieces of wood while you were "
                "offline. You have received 2,171,921 experience points for the Basic Wood Chopping skill.]\n"
                "Just as the rest of the players were struggling to survive in the zombie apocalyptic game, Fang Heng’s"
                " zombie clones were starting to clear every resource out of the forest.\n"
                "Hm… What an interesting game!"
            ),
            # Note: There are over a hundred chapters here, so I don't want to have to define all of them. I'll just
            #       assert that they are all chapter instances below.
            chapters=mock.ANY,
        )
        self.assertEqual(novel, expected_novel)

        # Assert that Novel.chapters looks like it should.
        self.assertEqual(len(novel.chapters), 983)
        self.assertTrue(
            all(isinstance(ch, Chapter) for ch in novel.chapters),
            "Novel.chapters needs to be a list of Chapter instances.",
        )
