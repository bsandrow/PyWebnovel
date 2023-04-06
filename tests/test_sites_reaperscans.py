import json
from unittest import TestCase, mock, skip

from bs4 import BeautifulSoup
import requests_mock

from webnovel.data import Chapter, Image, Novel, NovelStatus
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
        soup = BeautifulSoup('<div wire:id="abc">ABC</div>', "html.parser").find("div")
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


class ChapterListAPITestCase(TestCase):
    def test_current_page(self):
        json_data = json.dumps(
            reaperscans.build_chapter_list_request(page=1, path="/story/creepy-pasta-club", wire_id="DEF")
        )
        soup = BeautifulSoup(f"<div wire:id=\"DEF\" wire:initial-data='{json_data}'></div>", "html.parser").find("div")
        api = reaperscans.ChapterListAPI(
            app_url="https://reaperscans.com/", wire_id="DEF", element=soup, csrf_token="ABC"
        )
        self.assertEqual(api.current_page, 1)

    def test_next_page(self):
        json_data = json.dumps(
            reaperscans.build_chapter_list_request(page=1, path="/story/creepy-pasta-club", wire_id="DEF")
        )
        soup = BeautifulSoup(f"<div wire:id=\"DEF\" wire:initial-data='{json_data}'></div>", "html.parser").find("div")
        api = reaperscans.ChapterListAPI(
            app_url="https://reaperscans.com/", wire_id="DEF", element=soup, csrf_token="ABC"
        )
        with mock.patch.object(api, "make_call") as make_call, mock.patch.object(
            api, "update_page_history"
        ) as update_page_history:
            response = make_call.return_value = object()
            page_hist_response = update_page_history.return_value = object()
            return_val = api.next_page()
            self.assertEqual(return_val, page_hist_response)
            make_call.assert_called_once_with("nextPage", "page")
            update_page_history.assert_called_once_with(response)

    def test_previous_page(self):
        json_data = json.dumps(
            reaperscans.build_chapter_list_request(page=1, path="/story/creepy-pasta-club", wire_id="DEF")
        )
        soup = BeautifulSoup(f"<div wire:id=\"DEF\" wire:initial-data='{json_data}'></div>", "html.parser").find("div")
        api = reaperscans.ChapterListAPI(
            app_url="https://reaperscans.com/", wire_id="DEF", element=soup, csrf_token="ABC"
        )
        with mock.patch.object(api, "make_call") as make_call, mock.patch.object(
            api, "update_page_history"
        ) as update_page_history:
            response = make_call.return_value = object()
            page_hist_response = update_page_history.return_value = object()
            return_val = api.previous_page()
            self.assertEqual(return_val, page_hist_response)
            make_call.assert_called_once_with("prevPage", "page")
            update_page_history.assert_called_once_with(response)

    def test_get_page(self):
        json_data = json.dumps(
            reaperscans.build_chapter_list_request(page=1, path="/story/creepy-pasta-club", wire_id="DEF")
        )
        soup = BeautifulSoup(f"<div wire:id=\"DEF\" wire:initial-data='{json_data}'></div>", "html.parser").find("div")
        api = reaperscans.ChapterListAPI(
            app_url="https://reaperscans.com/", wire_id="DEF", element=soup, csrf_token="ABC"
        )
        with mock.patch.object(api, "make_call") as make_call, mock.patch.object(
            api, "update_page_history"
        ) as update_page_history:
            response = make_call.return_value = object()
            page_hist_response = update_page_history.return_value = object()
            return_val = api.get_page(5)
            self.assertEqual(return_val, page_hist_response)
            make_call.assert_called_once_with("gotoPage", 5, "page")
            update_page_history.assert_called_once_with(response)

    def test_update_page_history(self):
        json_data = json.dumps(
            reaperscans.build_chapter_list_request(page=1, path="/story/creepy-pasta-club", wire_id="DEF")
        )
        soup = BeautifulSoup(f"<div wire:id=\"DEF\" wire:initial-data='{json_data}'></div>", "html.parser").find("div")
        api = reaperscans.ChapterListAPI(
            app_url="https://reaperscans.com/", wire_id="DEF", element=soup, csrf_token="ABC"
        )
        html_obj = object()
        response = mock.Mock()
        response.json.return_value = {"serverMemo": {"data": {"page": 10}}, "effects": {"html": html_obj}}
        result = api.update_page_history(response=response)
        self.assertEqual(result, html_obj)
        self.assertEqual(api.page_history[10], html_obj)


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


class ReaperScansChapterScraperTestCase(TestCase):
    def test_get_limiter(self):
        self.assertEqual(reaperscans.ReaperScansChapterScraper().get_limiter(), reaperscans.LIMITER)


class RemoveTrailingHorizontalBarsFilterTestCase(TestCase):
    def test_filter(self):
        soup = BeautifulSoup(
            """
            <p>-------------</p>
            <div>  \t  </div>
            <p>  -----</p>
            <p>- abcd</p>
            <p>  -----</p>
            <div>  \t  </div>
            <p>-------------</p>
            """,
            "html.parser",
        )
        reaperscans.RemoveTrailingHorizontalBarsFilter().filter(soup)
        self.assertEqual(str(soup), "\n<p>-------------</p>\n<div> </div>\n<p>  -----</p>\n<p>- abcd</p>")


class RemoveStartingBannerFilterTestCase(TestCase):
    def test_filter(self):
        soup = BeautifulSoup(
            """
            <article>
            <p style="line-height: 2;"><strong>REAPER SCANS</strong></p>
            <p style="line-height: 2;">&nbsp;</p>
            <p style="line-height: 2;"><strong>Scary Story Club</strong></p>
            </article>
            """,
            "html.parser",
        ).find("article")
        reaperscans.RemoveStartingBannerFilter().filter(soup)
        self.assertEqual(
            str(soup),
            '<article>\n\n<p style="line-height: 2;">\u00A0</p>\n<p style="line-height: 2;"><strong>Scary Story Club</strong></p>\n</article>',
        )

    def test_filter_with_no_banner(self):
        soup = BeautifulSoup(
            """
            <article>
            <p style="line-height: 2;"><strong>CREEPER SCANS</strong></p>
            <p style="line-height: 2;">&nbsp;</p>
            <p style="line-height: 2;"><strong>Scary Story Club</strong></p>
            </article>
            """,
            "html.parser",
        ).find("article")
        reaperscans.RemoveStartingBannerFilter().filter(soup)
        self.assertEqual(
            str(soup),
            (
                "<article>\n"
                '<p style="line-height: 2;"><strong>CREEPER SCANS</strong></p>\n'
                '<p style="line-height: 2;">\u00A0</p>\n'
                '<p style="line-height: 2;"><strong>Scary Story Club</strong></p>\n'
                "</article>"
            ),
        )


class ReaperScansScraperTestCase(TestCase):
    maxDiff = None
    novel_url = "https://reaperscans.com/novels/1234-creepy-story-club"
    novel_page: str
    json_p1: str
    json_p2: str

    def test_get_novel_id(self):
        actual = reaperscans.ReaperScansScraper.get_novel_id("https://reaperscans.com/novels/1234-creepy-story-club")
        expected = "1234-creepy-story-club"
        self.assertEqual(actual, expected)

    def test_supports_url(self):
        supports_url = reaperscans.ReaperScansScraper.supports_url
        self.assertTrue(supports_url("https://reaperscans.com/novels/7145-creepy-story-club"))
        self.assertTrue(supports_url("https://www.reaperscans.com/novels/7145-creepy-story-club"))
        self.assertTrue(supports_url("http://www.reaperscans.com/novels/7145-creepy-story-club"))
        self.assertTrue(supports_url("http://www.reaperscans.com/novels/7145-creepy-story-club/"))
        self.assertFalse(supports_url("https://reaperscans.com/novels/creepy-story-club/"))

    @classmethod
    def setUpClass(cls):
        cls.novel_page = get_test_data("reaperscans_novel.html")
        cls.json_p1 = get_test_data("reaperscans_chlist_p1.json")
        cls.json_p2 = get_test_data("reaperscans_chlist_p2.json")

    def setUp(self):
        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        self.requests_mock.get("/novels/1234-creepy-story-club", text=self.novel_page)
        self.requests_mock.post(
            "/livewire/message/frontend.novel-chapters-list",
            additional_matcher=lambda r: r.json()["serverMemo"]["data"]["page"] == 1,
            text=self.json_p1,
        )
        self.requests_mock.post(
            "/livewire/message/frontend.novel-chapters-list",
            additional_matcher=lambda r: r.json()["serverMemo"]["data"]["page"] > 1,
            text=self.json_p2,
        )

    def tearDown(self):
        self.requests_mock.stop()

    def test_get_title(self):
        scraper = reaperscans.ReaperScansScraper()
        soup = scraper.get_soup(self.novel_page)
        self.assertEqual(scraper.get_title(soup), "Creepy Story Club")

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

    def test_get_chapters(self):
        scraper = reaperscans.ReaperScansScraper()
        soup = scraper.get_soup(self.novel_page)
        chapters = scraper.get_chapters(soup, self.novel_url)
        self.assertEqual(
            chapters,
            [
                Chapter(
                    url="https://reaperscans.com/novels/1234-creepy-story-club/chapters/12345678-chapter-3",
                    title="Chapter 3: Wrath of the Creeper (3)",
                    chapter_no=3,
                    slug="novel-chapter-list-12345678-chapter-3",
                ),
                Chapter(
                    url="https://reaperscans.com/novels/1234-creepy-story-club/chapters/23456789-chapter-4",
                    title="Chapter 4: Side Story: Creeper's Gonna Creep",
                    chapter_no=4,
                    slug="novel-chapter-list-23456789-chapter-4",
                ),
                Chapter(
                    url="https://reaperscans.com/novels/1234-creepy-story-club/chapters/5555-chapter-5",
                    title="Chapter 5: Creepypasta (1)",
                    chapter_no=5,
                    slug="novel-chapter-list-5555-chapter-5",
                ),
                Chapter(
                    url="https://reaperscans.com/novels/1234-creepy-story-club/chapters/6666-chapter-6",
                    title="Chapter 6: Creepypasta (2)",
                    chapter_no=6,
                    slug="novel-chapter-list-6666-chapter-6",
                ),
                Chapter(
                    url="https://reaperscans.com/novels/1234-creepy-story-club/chapters/7777-chapter-7",
                    title="Chapter 7: Creepypasta (3)",
                    chapter_no=7,
                    slug="novel-chapter-list-7777-chapter-7",
                ),
                Chapter(
                    url="https://reaperscans.com/novels/1234-creepy-story-club/chapters/8888-chapter-8",
                    title="Chapter 8: Apostle of the Creep",
                    chapter_no=8,
                    slug="novel-chapter-list-8888-chapter-8",
                ),
            ],
        )

    def test_scrape(self):
        scraper = reaperscans.ReaperScansScraper()
        novel = scraper.scrape(self.novel_url)
        page = scraper.get_page(self.novel_url)
        summary = scraper.get_summary(page)

        expected_novel = Novel(
            url=self.novel_url,
            site_id="ReaperScans.com",
            novel_id="1234-creepy-story-club",
            title="Creepy Story Club",
            status=NovelStatus.ONGOING,
            genres=[],
            author=None,
            summary=summary,
            cover_image=Image(url="https://reaperscans.com/imgs/creepy-story-club.jpg"),
            chapters=[
                Chapter(
                    url="https://reaperscans.com/novels/1234-creepy-story-club/chapters/12345678-chapter-3",
                    title="Chapter 3: Wrath of the Creeper (3)",
                    chapter_no=3,
                    slug="novel-chapter-list-12345678-chapter-3",
                ),
                Chapter(
                    url="https://reaperscans.com/novels/1234-creepy-story-club/chapters/23456789-chapter-4",
                    title="Chapter 4: Side Story: Creeper's Gonna Creep",
                    chapter_no=4,
                    slug="novel-chapter-list-23456789-chapter-4",
                ),
                Chapter(
                    url="https://reaperscans.com/novels/1234-creepy-story-club/chapters/5555-chapter-5",
                    title="Chapter 5: Creepypasta (1)",
                    chapter_no=5,
                    slug="novel-chapter-list-5555-chapter-5",
                ),
                Chapter(
                    url="https://reaperscans.com/novels/1234-creepy-story-club/chapters/6666-chapter-6",
                    title="Chapter 6: Creepypasta (2)",
                    chapter_no=6,
                    slug="novel-chapter-list-6666-chapter-6",
                ),
                Chapter(
                    url="https://reaperscans.com/novels/1234-creepy-story-club/chapters/7777-chapter-7",
                    title="Chapter 7: Creepypasta (3)",
                    chapter_no=7,
                    slug="novel-chapter-list-7777-chapter-7",
                ),
                Chapter(
                    url="https://reaperscans.com/novels/1234-creepy-story-club/chapters/8888-chapter-8",
                    title="Chapter 8: Apostle of the Creep",
                    chapter_no=8,
                    slug="novel-chapter-list-8888-chapter-8",
                ),
            ],
        )
        self.assertEqual(novel, expected_novel)
