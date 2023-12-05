import json

from bs4 import BeautifulSoup

from tests.helpers import ScraperTestCase
from webnovel import data, html
from webnovel.sites import skydemonorder


class NovelScraperTestCase(ScraperTestCase):
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
