from unittest import TestCase, mock

from bs4 import BeautifulSoup, Tag
import requests_mock

from webnovel.data import Chapter, Image, Novel, NovelStatus, Person
from webnovel.html import remove_element
from webnovel.sites import novelbin

from ..helpers import get_test_data

NOVEL_PAGE = get_test_data("novelbin/novel.html")
CHAPTER_PAGE = get_test_data("novelbin/chapter.html")
CHAPTER_LIST_PAGE = get_test_data("novelbin/chapterlist.html")


class CheckBackSoonFilterTestCase(TestCase):
    html = (
        "<div>\n"
        "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>\n"
        '<div class="schedule-text">The Novel will be updated first on this website. Come back and\n'
        " continue reading tomorrow, everyone!</div>\n"
        "</div>"
    )

    def test_removes_message(self):
        html = BeautifulSoup(self.html, "html.parser")
        novelbin.check_back_soon_filter(html)
        self.assertEqual(str(html), "<div>\n<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>\n\n</div>")


class NovelBinChapterScraperTestCase(TestCase):
    url: str = "https://novelbin.net/n/the-frozen-player-returns-nov906203625/cchapter-405-return-of-the-moon-4"

    def test_chapter_scraper(self):
        with requests_mock.Mocker() as m:
            m.get(self.url, text=CHAPTER_PAGE)
            scraper = novelbin.ChapterScraper()
            chapter = Chapter(url=self.url, title="Chapter 405. Return of the Moon (4)", chapter_no=405)
            self.assertIsNone(chapter.html)
            scraper.process_chapter(chapter)
            self.assertIsInstance(chapter.html, str)
            self.assertIn("Chapter 405. Return of the Moon (4)", CHAPTER_PAGE)
            self.assertNotIn("Chapter 405. Return of the Moon (4)", chapter.html)

    def test_chapter_scraper_without_title_in_content(self):
        with requests_mock.Mocker() as m:
            m.get(self.url, text=CHAPTER_PAGE.replace("Chapter 405. Return of", ""))
            scraper = novelbin.ChapterScraper()
            chapter = Chapter(url=self.url, title="Chapter 405. Return of the Moon (4)", chapter_no=405)
            self.assertIsNone(chapter.html)
            scraper.process_chapter(chapter)
            self.assertIsInstance(chapter.html, str)


class NovelBinScraperTestCase(TestCase):
    def test_get_novel_id_fails(self):
        scraper = novelbin.NovelScraper()
        self.assertIsNone(scraper.get_novel_id("https://example.com/"))

    def test_supports_url(self):
        self.assertTrue(novelbin.NovelScraper.supports_url("https://novelbin.net/n/the-frozen-player-returns"))
        self.assertTrue(novelbin.NovelScraper.supports_url("http://novelbin.net/n/the-frozen-player-returns"))
        self.assertTrue(novelbin.NovelScraper.supports_url("https://www.novelbin.net/n/the-frozen-player-returns"))
        self.assertTrue(novelbin.NovelScraper.supports_url("https://www.novelbin.net/n/the-frozen-player-returns/"))
        self.assertFalse(
            novelbin.NovelScraper.supports_url("https://www.novelbin.net/novel/the-frozen-player-returns/")
        )

    def test_get_title(self):
        scraper = novelbin.NovelScraper()
        soup = scraper.get_soup(NOVEL_PAGE)
        self.assertEqual(scraper.get_title(soup), "The Frozen Player Returns")

    def test_get_status(self):
        scraper = novelbin.NovelScraper()
        soup = scraper.get_soup(NOVEL_PAGE)
        self.assertEqual(scraper.get_status(soup), NovelStatus.ONGOING)

    def test_get_status_handles_unknown(self):
        scraper = novelbin.NovelScraper()
        soup = scraper.get_soup(NOVEL_PAGE)
        for item in soup.select(".col-novel-main > .col-info-desc > .desc > .info-meta > li"):
            remove_element(item)
        self.assertEqual(soup.select(".col-novel-main > .col-info-desc > .desc > .info-meta > li"), [])
        self.assertEqual(scraper.get_status(soup), NovelStatus.UNKNOWN)

    def test_get_genres(self):
        scraper = novelbin.NovelScraper()
        soup = scraper.get_soup(NOVEL_PAGE)
        self.assertEqual(
            scraper.get_genres(soup), ["Fantasy", "Shounen", "Adventure", "Supernatural", "Romance", "Action"]
        )

    def test_get_author(self):
        scraper = novelbin.NovelScraper()
        soup = scraper.get_soup(NOVEL_PAGE)
        self.assertEqual(scraper.get_author(soup), Person(name="제리엠", url="https://novelbin.net/a/제리엠"))

    def test_get_summary(self):
        scraper = novelbin.NovelScraper()
        soup = scraper.get_soup(NOVEL_PAGE)
        result = scraper.get_summary(soup)
        self.assertIsInstance(result, Tag)
        self.assertEqual(
            result.text.strip(),
            (
                "5 years after the world changed, the final boss appeared.\n\n"
                "[The final boss for area Earth, the Frost Queen, has appeared.] The final boss! If we can just defeat "
                "her, our lives will go back to normal!\n\n"
                "The top five players in the world, including Specter Seo Jun-ho, finally defeated the Frost Queen…\n\n"
                "But they fell into a deep slumber.\n\n"
                "25 years passed.\n\n"
                "«A second floor? It didn’t end when the Frost Queen died?\n\n"
                "Specter awakes from his slumber."
            ),
        )
        self.assertEqual(
            str(result),
            (
                '<div class="desc-text" itemprop="description">\n'
                "                                5 years after the world changed, the final boss appeared.\n\n"
                "[The final boss for area Earth, the Frost Queen, has appeared.] The final boss! If we can just defeat her, our lives will go back to normal!\n\n"
                "The top five players in the world, including Specter Seo Jun-ho, finally defeated the Frost Queen…\n\n"
                "But they fell into a deep slumber.\n\n"
                "25 years passed.\n\n"
                "«A second floor? It didn’t end when the Frost Queen died?\n\n"
                "Specter awakes from his slumber.\n"
                "                            </div>"
            ),
        )

    def test_get_chapters(self):
        scraper = novelbin.NovelScraper()
        soup = scraper.get_soup(NOVEL_PAGE)
        with requests_mock.Mocker() as m:
            m.get("/ajax/chapter-archive?novelId=the-frozen-player-returns", text=CHAPTER_LIST_PAGE)
            result = scraper.get_chapters(page=soup, url="https://novelbin.net/n/the-frozen-player-returns")

        self.assertEqual(
            result[0],
            Chapter(
                url="https://novelbin.net/n/the-frozen-player-returns/chapter-1-prologue",
                title="Chapter 1: Prologue",
                chapter_no=0,
                slug="chapter-1-prologue",
                html=None,
            ),
        )

    def test_scrape(self):
        with requests_mock.Mocker() as m:
            m.get("/n/the-frozen-player-returns", text=NOVEL_PAGE)
            m.get("/ajax/chapter-archive?novelId=the-frozen-player-returns", text=CHAPTER_LIST_PAGE)
            scraper = novelbin.NovelScraper()
            novel = scraper.scrape("https://novelbin.net/n/the-frozen-player-returns")
            soup = scraper.get_soup(NOVEL_PAGE)

        expected_novel = Novel(
            url="https://novelbin.net/n/the-frozen-player-returns",
            novel_id="the-frozen-player-returns",
            site_id="NovelBin.net",
            title="The Frozen Player Returns",
            status=NovelStatus.ONGOING,
            genres=["Fantasy", "Shounen", "Adventure", "Supernatural", "Romance", "Action"],
            author=Person(name="제리엠", url="https://novelbin.net/a/제리엠"),
            summary=scraper.get_summary(soup),
            cover_image=Image(url="https://media.novelbin.net/novel/the-frozen-player-returns.jpg"),
            # Note: There are over a hundred chapters here, so I don't want to have to define all of them. I'll just
            #       assert that they are all chapter instances below.
            extras={"Rating": "7.9 out of 10 [259 vote(s)]"},
            published_on=None,
            last_updated_on=None,
            chapters=mock.ANY,
            extra_css=novelbin.NovelScraper.extra_css,
        )

        self.assertEqual(novel, expected_novel)

        # Assert that Novel.chapters looks like it should.
        self.assertEqual(len(novel.chapters), 309)
        self.assertTrue(
            all(isinstance(ch, Chapter) for ch in novel.chapters),
            "Novel.chapters needs to be a list of Chapter instances.",
        )
