from tests.helpers import ScraperTestCase
from webnovel import data, scraping


class DummyScraper(scraping.WpMangaNovelInfoMixin, scraping.NovelScraperBase):
    site_name = "Dummy"


class WpMangaMixinTestCase(ScraperTestCase):
    maxDiff = None
    template_defaults = {
        "wp-manga-header.html.j2": {
            "status": "OnGoing",
            "summary": "$SUMMARY$",
            "cover_image_url": "$COVER_IMAGE_URL$",
            "title": "$TITLE$",
            "author": {
                "name": "$AUTHOR$",
                "url": "$AUTHOR_URL$",
            },
            "tags": [
                {"url": ":tag:based on book:", "name": "Based on a Book"},
            ],
            "genres": [
                {"url": ":genre:comdy:", "name": "Comedy"},
                {"url": ":genre:tragedy:", "name": "Tragedy"},
            ],
        }
    }
    default_template = "wp-manga-header.html.j2"

    def test_title(self):
        scraper = DummyScraper()
        page = self.get_page()
        actual = scraper.get_title(page)
        expected = "$TITLE$"
        self.assertEqual(actual, expected)

    def test_status(self):
        scraper = DummyScraper()
        page = self.get_page()
        actual = scraper.get_status(page)
        expected = data.NovelStatus.ONGOING
        self.assertEqual(actual, expected)

    def test_author(self):
        scraper = DummyScraper()
        page = self.get_page()
        actual = scraper.get_author(page)
        expected = data.Person(name="$AUTHOR$", url="$AUTHOR_URL$")
        self.assertEqual(actual, expected)

    def test_tags(self):
        scraper = DummyScraper()
        page = self.get_page()
        actual = scraper.get_tags(page)
        expected = ["Based on a Book"]
        self.assertEqual(actual, expected)

    def test_genres(self):
        scraper = DummyScraper()
        page = self.get_page()
        actual = scraper.get_genres(page)
        expected = ["Comedy", "Tragedy"]
        self.assertEqual(actual, expected)

    def test_cover_image(self):
        scraper = DummyScraper()
        page = self.get_page()
        actual = scraper.get_cover_image(page)
        expected = data.Image(url="$COVER_IMAGE_URL$")
        self.assertEqual(actual, expected)
