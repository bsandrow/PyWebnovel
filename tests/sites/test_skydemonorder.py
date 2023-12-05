import datetime
import json
from unittest import mock

from bs4 import BeautifulSoup

from tests.helpers import ScraperTestCase
from webnovel import data, html
from webnovel.sites import skydemonorder


class NovelScraperTestCase(ScraperTestCase):
    maxDiff = None
    template_defaults = {
        "skydemonorder-1.html.j2": {
            "status": "$STATUS$",
            "summary": "$SUMMARY$",
            "cover_image_url": "$COVER_IMAGE_URL$",
            "title": "$TITLE$",
            "sections": [],
        }
    }
    default_template = "skydemonorder-1.html.j2"

    @staticmethod
    def generate_section(title: str, as_a_dict: bool = False, chapters: list | None = None) -> tuple[str, dict]:
        data = [
            {
                "full_title": chapter["title"],
                "slug": chapter["title"].lower().replace(" ", "-"),
                "project": {"slug": "name-of-novel-slug", "is_mature": False},
                "views": 10582,
                "posted_at": chapter.get("posted_at", "2021-12-11"),
                "is_mature": False,
                "has_images": False,
            }
            for chapter in chapters or []
        ]

        if as_a_dict:
            data = {str(key): item for key, item in enumerate(data, start=1)}

        return (
            title,
            (
                " {\n"
                "   expanded: 1,\n"
                "   sortOrder: 'desc',\n"
                "   chapters: (function(data) {\n"
                "       if (!Array.isArray(data)) {\n"
                "           data = Object.values(data);\n"
                "       }\n"
                "       return data;\n"
                "   })(" + json.dumps(data) + ")\n"
                " }\n"
            ),
        )

    def test_novel_data_from_section_as_list(self):
        scraper = skydemonorder.NovelScraper()
        section = self.generate_section(
            title="Episodes",
            chapters=[{"title": "Ep 2 The Ending"}, {"title": "Ep 1 The Beginning"}],
        )
        page = self.get_page(sections=[section])
        actual = scraper.get_novel_data_from_section(page=page, pattern=r"Episodes")
        expected = [
            {
                "full_title": "Ep 1 The Beginning",
                "slug": "ep-1-the-beginning",
                "project": {"slug": "name-of-novel-slug", "is_mature": False},
                "views": 10582,
                "posted_at": "2021-12-11",
                "is_mature": False,
                "has_images": False,
            },
            {
                "full_title": "Ep 2 The Ending",
                "slug": "ep-2-the-ending",
                "project": {"slug": "name-of-novel-slug", "is_mature": False},
                "views": 10582,
                "posted_at": "2021-12-11",
                "is_mature": False,
                "has_images": False,
            },
        ]
        self.assertEqual(actual, expected)

    def test_novel_data_from_section_as_dict(self):
        scraper = skydemonorder.NovelScraper()
        section = self.generate_section(
            title="Free Episodes",
            as_a_dict=True,
            chapters=[{"title": "Ep 2 The Ending"}, {"title": "Ep 1 The Beginning"}],
        )
        page = self.get_page(sections=[section])
        actual = scraper.get_novel_data_from_section(page=page, pattern=r"(Free\s+?)?Episodes")
        expected = [
            {
                "full_title": "Ep 1 The Beginning",
                "slug": "ep-1-the-beginning",
                "project": {"slug": "name-of-novel-slug", "is_mature": False},
                "views": 10582,
                "posted_at": "2021-12-11",
                "is_mature": False,
                "has_images": False,
            },
            {
                "full_title": "Ep 2 The Ending",
                "slug": "ep-2-the-ending",
                "project": {"slug": "name-of-novel-slug", "is_mature": False},
                "views": 10582,
                "posted_at": "2021-12-11",
                "is_mature": False,
                "has_images": False,
            },
        ]
        self.assertEqual(actual, expected)

    def test_cover_image(self):
        scraper = skydemonorder.NovelScraper()
        page = self.get_page()
        actual = scraper.get_cover_image(page)
        expected = data.Image(url="$COVER_IMAGE_URL$")
        self.assertEqual(actual, expected)

    def test_title(self):
        scraper = skydemonorder.NovelScraper()
        page = self.get_page(title="Hell’s Handbook")
        actual = scraper.get_title(page)
        expected = "Hell’s Handbook"
        self.assertEqual(actual, expected)

    def test_summary(self):
        scraper = skydemonorder.NovelScraper()
        page = self.get_page()
        actual = scraper.get_summary(page)
        expected = '<div class="prose"><span>$SUMMARY$</span></div>'
        self.assertEqual(str(actual), expected)

    def test_author_with_title_in_list(self):
        scraper = skydemonorder.NovelScraper()
        page = self.get_page(title="Hell’s Handbook")
        self.assertIn("Hell’s Handbook", skydemonorder.TITLE_AUTHOR_MAP)
        actual = scraper.get_author(page=page)
        expected = data.Person(name="年末")
        self.assertEqual(actual, expected)

    def test_author_with_title_not_in_list(self):
        scraper = skydemonorder.NovelScraper()
        title = "$NOT IN LIST$"
        page = self.get_page(title=title)
        self.assertNotIn(title, skydemonorder.TITLE_AUTHOR_MAP)
        actual = scraper.get_author(page)
        expected = None
        self.assertEqual(actual, expected)

    def test_get_status_not_in_map(self):
        scraper = skydemonorder.NovelScraper()
        page = self.get_page(status="???")
        actual = scraper.get_status(page)
        expected = data.NovelStatus.UNKNOWN
        self.assertEqual(actual, expected)

    def test_get_status_in_map(self):
        scraper = skydemonorder.NovelScraper()
        page = self.get_page(status="OnGoing")
        actual = scraper.get_status(page)
        expected = data.NovelStatus.ONGOING
        self.assertEqual(actual, expected)

    def test_post_processing(self):
        scraper = skydemonorder.NovelScraper()
        with mock.patch.object(scraper, "get_page") as m:
            sections = [
                self.generate_section(
                    title="Paid Episodes", chapters=[{"title": "Ep 3 The Next Day", "posted_at": "2011-01-01"}]
                ),
                self.generate_section(
                    title="Free Episodes",
                    chapters=reversed([{"title": "Ep 1 The Beginning"}, {"title": "Ep 2 The Ending"}]),
                ),
            ]

            m.return_value = self.get_page(sections=sections)
            novel = scraper.scrape("https://skydemonorder.com/projects/novel-id")
            self.assertEqual(novel.title, "$TITLE$")

            today = datetime.date.today().strftime("%Y-%m-%d")
            self.assertEqual(novel.extras["Views"], f"10,601 view(s) (as of {today})")
            self.assertEqual(novel.translator, data.Person(name="SkyDemonOrder", url="https://skydemonorder.com/"))
            self.assertEqual(novel.published_on, datetime.date(2006, 1, 1))
            self.assertEqual(
                novel.extras["release_schedule"],
                [
                    {
                        "release_date": datetime.datetime(2011, 1, 1, 0, 0),
                        "title": "Ep 3 The Next Day",
                        "url": "https://skydemonorder.com/projects/name-of-novel-slug/ep-3-the-next-day",
                    }
                ],
            )
            self.assertEqual(
                novel.chapters,
                [
                    data.Chapter(
                        url="https://skydemonorder.com/projects/name-of-novel-slug/ep-1-the-beginning",
                        title="Ep 1 The Beginning",
                        chapter_no=0,
                        pub_date=datetime.datetime(2021, 12, 11),
                    ),
                    data.Chapter(
                        url="https://skydemonorder.com/projects/name-of-novel-slug/ep-2-the-ending",
                        title="Ep 2 The Ending",
                        chapter_no=1,
                        pub_date=datetime.datetime(2021, 12, 11),
                    ),
                ],
            )


class ChapterScraperTestCase(ScraperTestCase):
    default_template = "skydemonorder-2.html.j2"

    def test_chapter_content(self):
        scraper = skydemonorder.ChapterScraper()
        with mock.patch.object(scraper, "get_page") as m:
            m.return_value = self.get_page()
            chapter = data.Chapter(
                url="doesnotmatter",
                title="Does Not Matter",
            )
            scraper.process_chapter(chapter)
            self.assertEqual(
                chapter.html,
                (
                    '<div class="prose">\n'
                    '<div wire:effects="" wire:id="" wire:snapshot="" x-data="" x-init="">\n'
                    '<div wire:ignore="">\n'
                    "<p>Example</p>\n"
                    "<p>Content</p>\n"
                    "</div>\n"
                    "</div>\n"
                    "</div>"
                ),
            )
