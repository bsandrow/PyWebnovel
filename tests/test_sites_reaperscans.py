from unittest import TestCase, mock, skip

from bs4 import BeautifulSoup
import requests_mock

from webnovel.data import Chapter, Novel, NovelStatus
from webnovel.sites import reaperscans

from .helpers import get_test_data


class GetCsrfTokenTestCase(TestCase):
    novel_page: str

    @classmethod
    def setUpClass(cls):
        cls.novel_page = get_test_data("reaperscans_novel.html")

    def test_extracts_csrf_token(self):
        soup = BeautifulSoup(self.novel_page, "html.parser")
        actual = reaperscans.get_csrf_token(soup)
        expected = "9DQroQWIrwO7dV7lV8P5LRx1H7RT5hc90UzLVNrj"
        self.assertEqual(actual, expected)


class GetWireIdTestCase(TestCase):
    def test_extracts_wire_id_from_top_level_element(self):
        soup = BeautifulSoup('<div wire:id="abc">ABC</div>', "html.parser")
        actual = reaperscans.get_wire_id(soup)
        expected = "abc"
        self.assertEqual(actual, expected)

    def test_extracts_wire_id_from_sub_elements(self):
        soup = BeautifulSoup('<div><p wire:id="def">ABC</p></div>', "html.parser")
        actual = reaperscans.get_wire_id(soup)
        expected = "def"
        self.assertEqual(actual, expected)

    def test_handles_multiple_wire_ids(self):
        soup = BeautifulSoup('<div><p wire:id="def">ABC</p><p wire:id="ghi">DEF</p></div>', "html.parser")
        with self.assertRaises(ValueError):
            reaperscans.get_wire_id(soup)


class BuildChapterListRequestTestCase(TestCase):
    def test_happy_path(self):
        actual = reaperscans.build_chapter_list_request(page=2, path=":PATH:", wire_id=":WIRE_ID:", locale=":LOCALE:")
        expected = {
            "fingerprint": {
                "id": ":WIRE_ID:",
                "locale": ":LOCALE:",
                "method": "GET",
                "name": "frontend.novel-chapters-list",
                "path": ":PATH:",
                "v": "acj",
            },
            "serverMemo": {
                "checksum": None,  # TODO
                "children": [],
                "data": {"novel": [], "page": 2, "paginators": {"page": 2}},
                "dataMeta": {
                    "models": {
                        "novel": {
                            "class": "App\\Models\\Novel",
                            "collectionClass": None,
                            "connection": "pgsql",
                            "id": None,  # TODO  novel id can pull from cover image URL
                            "relations": [],
                        }
                    }
                },
                "errors": [],
                "htmlHash": None,  # TODO
            },
            "updates": [
                {
                    "payload": {
                        "id": None,  # TODO
                        "method": "gotoPage",
                        "params": [1, "page"],
                    },
                    "type": "callMethod",
                }
            ],
        }
        self.assertEqual(actual, expected)


class ReaperScansScraperTestCase(TestCase):
    maxDiff = None
    novel_url = "https://reaperscans.com/novels/7666-player-who-returned-10000-years-later"
    novel_page: str
    chlist_page_1: str
    chlist_page_2: str
    chlist_page_3: str
    chlist_page_4: str

    def test_validate_url(self):
        self.assertTrue(
            reaperscans.ReaperScansScraper.validate_url("https://reaperscans.com/novels/7145-max-talent-player")
        )
        self.assertTrue(
            reaperscans.ReaperScansScraper.validate_url("https://www.reaperscans.com/novels/7145-max-talent-player")
        )
        self.assertTrue(
            reaperscans.ReaperScansScraper.validate_url("http://www.reaperscans.com/novels/7145-max-talent-player")
        )
        self.assertTrue(
            reaperscans.ReaperScansScraper.validate_url("http://www.reaperscans.com/novels/7145-max-talent-player/")
        )
        self.assertFalse(
            reaperscans.ReaperScansScraper.validate_url("https://reaperscans.com/novels/max-talent-player/")
        )

    @classmethod
    def setUpClass(cls):
        cls.novel_page = get_test_data("reaperscans_novel.html")
        cls.chlist_page_1 = get_test_data("reaperscans_chlist_p1.html")  # 22 free chapters + 10 paid chapters
        cls.chlist_page_2 = get_test_data("reaperscans_chlist_p2.html")  # 32 free chapters
        cls.chlist_page_3 = get_test_data("reaperscans_chlist_p3.html")  # 2 free chapters
        cls.chlist_page_4 = get_test_data("reaperscans_chlist_p4.html")  # 0 chapters

    def setUp(self):
        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        self.requests_mock.get("/novels/7666-player-who-returned-10000-years-later", text=self.novel_page)
        self.requests_mock.get("/novels/7666-player-who-returned-10000-years-later?page=1", text=self.chlist_page_1)
        self.requests_mock.get("/novels/7666-player-who-returned-10000-years-later?page=2", text=self.chlist_page_2)
        self.requests_mock.get("/novels/7666-player-who-returned-10000-years-later?page=3", text=self.chlist_page_3)
        self.requests_mock.get("/novels/7666-player-who-returned-10000-years-later?page=4", text=self.chlist_page_4)

    def tearDown(self):
        self.requests_mock.stop()

    def test_get_title(self):
        scraper = reaperscans.ReaperScansScraper()
        soup = scraper.get_soup(self.novel_page)
        self.assertEqual(scraper.get_title(soup), "Player Who Returned 10,000 Years Later")

    def test_get_status(self):
        scraper = reaperscans.ReaperScansScraper()
        soup = scraper.get_soup(self.novel_page)
        self.assertEqual(scraper.get_status(soup), NovelStatus.ONGOING)

    def test_get_genres(self):
        scraper = reaperscans.ReaperScansScraper()
        soup = scraper.get_soup(self.novel_page)
        self.assertEqual(scraper.get_genres(soup), [])

    def test_get_author(self):
        scraper = reaperscans.ReaperScansScraper()
        soup = scraper.get_soup(self.novel_page)
        self.assertIsNone(scraper.get_author(soup))

    def test_get_summary(self):
        scraper = reaperscans.ReaperScansScraper()
        soup = scraper.get_soup(self.novel_page)
        result = scraper.get_summary(soup)
        self.assertEqual(
            result.text.strip(),
            (
                "One day, KangWoo suddenly fell into Hell, with only a strong desire to survive and the Authority "
                "of Predation on him.\n\n"
                "All the way from the 1st to the 9th hell, he devoured hundreds of thousands of demons,\n"
                "until even the seven archdukes finally knelt before him.\n\n"
                '"Why do you wish to return? Do you not already possess everything in Hell, my lord?"\n\n'
                '“What exactly is it that I have?"\n\n'
                "There was nothing to eat, nor any entertainment!\n"
                "Desolate lands and hideous demons were all that filled Hell.\n\n"
                "\"I'm going back.”\n\n"
                "After ten thousand years in the 9 hells, he returns to Earth at last."
            ),
        )

    @skip
    def test_get_chapters(self):
        scraper = reaperscans.ReaperScansScraper()
        soup = scraper.get_soup(self.novel_page)
        chapters = scraper.get_chapters(soup, self.novel_url)
        chapter = chapters[0]
        chapter_url = (
            "https://reaperscans.com/novels/7666-player-who-returned-10000-years-later/chapters/79444921-chapter-152"
        )
        self.assertEqual(
            chapter,
            Chapter(
                url=chapter_url,
                title="Chapter 152 - Demon King Balzac (1)",
                chapter_no="152",
            ),
        )

    @skip
    def test_scrape(self):
        scraper = reaperscans.ReaperScansScraper()
        novel = scraper.scrape(self.novel_url)
        page = scraper.get_page(self.novel_url)
        summary = scraper.get_summary(page)

        expected_novel = Novel(
            url=self.novel_url,
            site_id="ReaperScans.com",
            novel_id="",
            title="Player Who Returned 10,000 Years Later",
            status=NovelStatus.ONGOING,
            genres=[],
            author=None,
            summary=summary,
            # Note: There are over a hundred chapters here, so I don't want to have to define all of them. I'll just
            #       assert that they are all chapter instances below.
            chapters=mock.ANY,
        )
        self.assertEqual(novel, expected_novel)

        # Assert that Novel.chapters looks like it should.
        self.assertEqual(len(novel.chapters), 56)  # 22 + 32 + 2
        self.assertTrue(
            all(isinstance(ch, Chapter) for ch in novel.chapters),
            "Novel.chapters needs to be a list of Chapter instances.",
        )