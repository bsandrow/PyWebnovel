from unittest import mock, TestCase

import requests_mock

from webnovel.data import Novel, NovelStatus, Person, Chapter
from webnovel.sites import novelbin
from ..helpers import get_test_data


class NovelBinTestCase(TestCase):
    def test_validate_url(self):
        self.assertTrue(novelbin.validate_url("https://novelbin.net/n/the-frozen-player-returns"))
        self.assertTrue(novelbin.validate_url("http://novelbin.net/n/the-frozen-player-returns"))
        self.assertTrue(novelbin.validate_url("https://www.novelbin.net/n/the-frozen-player-returns"))
        self.assertTrue(novelbin.validate_url("https://www.novelbin.net/n/the-frozen-player-returns/"))
        self.assertFalse(novelbin.validate_url("https://www.novelbin.net/novel/the-frozen-player-returns/"))


class NovelBinScraperTestCase(TestCase):
    novel_page: str
    chlist_page: str

    @classmethod
    def setUpClass(cls):
        cls.novel_page = get_test_data("novelbin_novel.html")
        cls.chlist_page = get_test_data("novelbin_chapterlist.html")

    def test_get_title(self):
        scraper = novelbin.NovelBinScraper()
        soup = scraper.get_soup(self.novel_page)
        self.assertEqual(scraper.get_title(soup), "The Frozen Player Returns")

    def test_get_status(self):
        scraper = novelbin.NovelBinScraper()
        soup = scraper.get_soup(self.novel_page)
        self.assertEqual(scraper.get_status(soup), NovelStatus.ONGOING)

    def test_get_genres(self):
        scraper = novelbin.NovelBinScraper()
        soup = scraper.get_soup(self.novel_page)
        self.assertEqual(
            scraper.get_genres(soup),
            ["Fantasy", "Shounen", "Adventure", "Supernatural", "Romance", "Action"]
        )

    def test_get_author(self):
        scraper = novelbin.NovelBinScraper()
        soup = scraper.get_soup(self.novel_page)
        self.assertEqual(
            scraper.get_author(soup),
            Person(name="제리엠", url="https://novelbin.net/a/제리엠")
        )

    def test_get_summary(self):
        scraper = novelbin.NovelBinScraper()
        soup = scraper.get_soup(self.novel_page)
        self.assertEqual(
            scraper.get_summary(soup),
            (
                "5 years after the world changed, the final boss appeared.\n\n"
                "[The final boss for area Earth, the Frost Queen, has appeared.] The final boss! If we can just defeat "
                "her, our lives will go back to normal!\n\n"
                "The top five players in the world, including Specter Seo Jun-ho, finally defeated the Frost Queen…\n\n"
                "But they fell into a deep slumber.\n\n"
                "25 years passed.\n\n"
                "«A second floor? It didn’t end when the Frost Queen died?\n\n"
                "Specter awakes from his slumber."
            )
        )

    def test_get_chapters(self):
        scraper = novelbin.NovelBinScraper()
        soup = scraper.get_soup(self.novel_page)
        with requests_mock.Mocker() as m:
            m.get("/ajax/chapter-archive?novelId=the-frozen-player-returns", text=self.chlist_page)
            result = scraper.get_chapters(page=soup, url="https://novelbin.net/n/the-frozen-player-returns")

        self.assertEqual(
            result[0],
            Chapter(
                url="https://novelbin.net/n/the-frozen-player-returns/chapter-1-prologue",
                title="Chapter 1. Prologue",
                chapter_no="1",
            )
        )

    def test_scrape(self):
        with requests_mock.Mocker() as m:
            m.get("/n/the-frozen-player-returns", text=self.novel_page)
            m.get("/ajax/chapter-archive?novelId=the-frozen-player-returns", text=self.chlist_page)
            scraper = novelbin.NovelBinScraper()
            novel = scraper.scrape("https://novelbin.net/n/the-frozen-player-returns")

        expected_novel = Novel(
            url="https://novelbin.net/n/the-frozen-player-returns",
            title="The Frozen Player Returns",
            status=NovelStatus.ONGOING,
            genres=["Fantasy", "Shounen", "Adventure", "Supernatural", "Romance", "Action"],
            author=Person(name="제리엠", url="https://novelbin.net/a/제리엠"),
            summary=(
                "5 years after the world changed, the final boss appeared.\n\n"
                "[The final boss for area Earth, the Frost Queen, has appeared.] The final boss! If we can just defeat "
                "her, our lives will go back to normal!\n\n"
                "The top five players in the world, including Specter Seo Jun-ho, finally defeated the Frost Queen…\n\n"
                "But they fell into a deep slumber.\n\n"
                "25 years passed.\n\n"
                "«A second floor? It didn’t end when the Frost Queen died?\n\n"
                "Specter awakes from his slumber."
            ),
            # Note: There are over a hundred chapters here, so I don't want to have to define all of them. I'll just
            #       assert that they are all chapter instances below.
            chapters=mock.ANY
        )
        self.assertEqual(novel, expected_novel)

        # Assert that Novel.chapters looks like it should.
        self.assertTrue(len(novel.chapters) == 309, "Novel.chapters should have 309 chapters.")
        self.assertTrue(
            all(isinstance(ch, Chapter) for ch in novel.chapters),
            "Novel.chapters needs to be a list of Chapter instances."
        )
