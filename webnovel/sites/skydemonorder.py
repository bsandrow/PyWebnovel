"""SkyDemonOrder.com scrapers and utilities."""

import datetime
import logging
import re

from webnovel import data, errors, html, logs, scraping

SITE_NAME = "SkyDemonOrder.org"
logger = logging.getLogger(__name__)
timer = logs.LogTimer(logger)


class SkyDemonOrderChapterScraper(scraping.ChapterScraper):
    """Chapter Scraper for SkyDemonOrder.com Content."""

    site_name = SITE_NAME
    url_pattern = scraping.HTTPS_PREFIX + r"skydemonorder\.com/projects/(?P<ChapterID>(?P<NovelID>[\w\d-]+)/[\w\d-]+)"
    content_selector = scraping.Selector("main .prose")


class SkyDemonOrderNovelScraper(scraping.NovelScraperBase):
    """Novel Scraper for SkyDemonOrder.com Content."""

    site_name = SITE_NAME
    url_pattern = scraping.HTTPS_PREFIX + r"skydemonorder\.com/projects/(?P<NovelID>[\w\d-]+)"
    title_selector = scraping.Selector("header > div > h1")
    status_map = {"complete": data.NovelStatus.COMPLETED, "ongoing": data.NovelStatus.ONGOING}

    def get_status(self, page) -> data.NovelStatus:
        """Extract the novel's status from the page."""
        for item in page.select("header > div > p"):
            if match := re.match(r"Status:\s+(\w+)", item.text, re.IGNORECASE):
                return self.status_map.get(match.group(1).lower(), data.NovelStatus.UNKNOWN)
        return data.NovelStatus.UNKNOWN

    def get_author(self, page):
        """
        Return None since SkyDemonOrder doesn't list the author.

        Since they have a limited number of projects, I'll manually add some of
        the authors here.
        """
        title = self.get_title(page)
        return {
            "Your Majesty, Please Don't Kill Me Again": None,
            "Questioning Heaven, Desiring the Way": data.Person(name="雾非雪"),
            "Hell’s Handbook": data.Person(name="年末"),
            "The Shadowed Legacy of the Soulless Messenger": data.Person(name="Hong Jung-Hoon (홍정훈)"),
            "Requiem of Subdued Souls": data.Person(name="정연"),
            "Clearing the Game at the End of the World": data.Person(name="첨G"),
            "The Return of the Crazy Demon": data.Person(name="yu jinsung (유진성)"),
            "Absolute Sword Sense": data.Person(name="한중월야"),
            "Invincible Mumu": data.Person(name="한중월야"),
            "Return of the Mount Hua Sect": data.Person(name="비가"),
            "The Dark Magician Transmigrates After 66666 Years": data.Person(name="화봉"),
            "Heavenly Demon Cultivation Simulation": data.Person(name="조형근"),
            "The Heavenly Demon Can’t Live a Normal Life": data.Person(name="Sancheon"),
            "Reformation of the Deadbeat Noble": data.Person(name="이등별"),
            "Descent of the Demon God": data.Person(name="한중월야"),
        }.get(title)

    def get_summary(self, page):
        """Extract the novel's summary from the page."""
        desc = self._find_description_heading(page)
        return desc.parent.select_one(".prose") if desc else None

    def _find_description_heading(self, page: scraping.BeautifulSoup) -> scraping.Tag:
        """Find and extract the 'Description' heading from the page."""
        for h2 in page.find_all("h2"):
            if h2.text.strip().lower() == "description":
                return h2
        return None

    def post_processing(self, page, url, novel):
        """Extra View/Last Update Information."""
        novel.extras = novel.extras or {}
        description = self._find_description_heading(page)
        if description is not None:
            for div in description.find_all("div", recursive=False):
                name = div.find("strong").text.strip()
                value = div.find("span").text.strip()
                if name == "Views":
                    novel.extras["Views"] = f"{value} view(s) (as of {datetime.date.today:%Y-%m-%d})"
                if name == "Last Update":
                    novel.published_on = datetime.datetime.strptime(value, "%Y-%m-%d").date()

        # Note: Unlike some other sites on which author's self-publish or sites
        # that scrape content from the original sources, SkyDemonOrder is a translation
        # group, so we can just blindly set them as the translator for stories scraped
        # from their site.
        novel.translator = data.Person(name="SkyDemonOrder", url="https://skydemonorder.com/")

    def get_cover_image(self, page):
        """Get cover image url."""
        images = page.select("main img")
        assert len(images) == 1, "Expected to only find one <img> tag on novel page."
        image = images[0]
        return data.Image(url=image.get("src"))

    def get_chapters(self, page, url):
        """Return the list of chapters from the page."""
        sections = page.select("section")
        chapter_els = []

        for section in sections:
            h3 = section.find("h3")
            # Note: novels with paid & free chapters will have the free chapters
            #       listed as "Free Chapters", but for the completed novels that
            #       section is just labelled "Chapters" since there are no paid
            #       chapters.
            if h3 and h3.text.strip() in ("Free Chapters", "Chapters"):
                chapter_els = reversed(section.select("div > div> div.items-center > a"))

        return [
            data.Chapter(chapter_no=idx, url=chapter_el.get("href"), title=chapter_el.text.strip())
            for idx, chapter_el in enumerate(chapter_els)
        ]
