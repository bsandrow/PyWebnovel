from unittest import TestCase

from bs4 import BeautifulSoup

from webnovel import data, html
from webnovel.sites import readwn

from .helpers import get_test_data

NOVEL_INFO = get_test_data("readwn/novel_info.html")


class ReadWNNovelTestCase(TestCase):
    def test_get_status_completed(self):
        page = BeautifulSoup(NOVEL_INFO, "html.parser")
        self.assertIn("Ongoing", str(page))
        for el in page("strong"):
            if el.text.strip().lower() == "ongoing":
                el.string = "Completed"
        self.assertNotIn("Ongoing", str(page))
        scraper = readwn.ReadWnNovelScraper()
        result = scraper.get_status(page)
        expected = data.NovelStatus.COMPLETED
        self.assertEqual(result, expected)

    def test_get_status_ongoing(self):
        page = BeautifulSoup(NOVEL_INFO, "html.parser")
        scraper = readwn.ReadWnNovelScraper()
        result = scraper.get_status(page)
        expected = data.NovelStatus.ONGOING
        self.assertEqual(result, expected)

    def test_get_status_unknown_value(self):
        page = BeautifulSoup(NOVEL_INFO, "html.parser")
        self.assertIn("Ongoing", str(page))
        for el in page("strong"):
            if el.text.strip().lower() == "ongoing":
                el.string = "???"
        self.assertNotIn("Ongoing", str(page))
        scraper = readwn.ReadWnNovelScraper()
        result = scraper.get_status(page)
        expected = data.NovelStatus.UNKNOWN
        self.assertEqual(result, expected)

    def test_get_status_missing_value(self):
        page = BeautifulSoup(NOVEL_INFO, "html.parser")
        for el in page("small"):
            if el.text.strip().lower() == "status":
                el.string = "???"
        self.assertIn("Ongoing", str(page))
        self.assertNotIn("Status", str(page))
        scraper = readwn.ReadWnNovelScraper()
        result = scraper.get_status(page)
        expected = data.NovelStatus.UNKNOWN
        self.assertEqual(result, expected)

    def test_get_status_no_header_stats(self):
        page = BeautifulSoup(NOVEL_INFO, "html.parser")
        el = page.select_one(".header-stats")
        html.remove_element(el)
        scraper = readwn.ReadWnNovelScraper()
        result = scraper.get_status(page)
        expected = data.NovelStatus.UNKNOWN
        self.assertEqual(result, expected)

    def test_get_author(self):
        page = BeautifulSoup(NOVEL_INFO, "html.parser")
        scraper = readwn.ReadWnNovelScraper()
        result = scraper.get_author(page)
        expected = data.Person(name="海贼xx火...")
        self.assertEqual(result, expected)

    def test_get_author_blank(self):
        page = BeautifulSoup(NOVEL_INFO.replace("海贼xx火...", ""), "html.parser")
        scraper = readwn.ReadWnNovelScraper()
        result = scraper.get_author(page)
        self.assertIsNone(result)

    def test_get_author_missing_block(self):
        page = BeautifulSoup(NOVEL_INFO, "html.parser")
        el = page.select_one(".author")
        html.remove_element(el)
        scraper = readwn.ReadWnNovelScraper()
        result = scraper.get_author(page)
        self.assertIsNone(result)

    def test_get_title(self):
        page = BeautifulSoup(NOVEL_INFO, "html.parser")
        scraper = readwn.ReadWnNovelScraper()
        result = scraper.get_title(page)
        expected = "I, the deputy emperor of the Red Tuan, was overheard by the red hair"
        self.assertEqual(result, expected)
