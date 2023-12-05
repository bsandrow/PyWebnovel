"""SkyDemonOrder.com scrapers and utilities."""

import datetime
import json
import logging
import re
import urllib.parse

from bs4 import BeautifulSoup, Tag

from webnovel import data, logs, scraping

SITE_NAME = "SkyDemonOrder.org"
logger = logging.getLogger(__name__)
timer = logs.LogTimer(logger)

TITLE_AUTHOR_MAP = {
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
}


class ChapterScraper(scraping.ChapterScraperBase):
    """Chapter Scraper for SkyDemonOrder.com Content."""

    site_name = SITE_NAME
    url_pattern = scraping.HTTPS_PREFIX + r"skydemonorder\.com/projects/(?P<ChapterID>(?P<NovelID>[\w\d-]+)/[\w\d-]+)"
    content_selector = scraping.Selector("main .prose")


class NovelScraper(scraping.NovelScraperBase):
    """Novel Scraper for SkyDemonOrder.com Content."""

    site_name = SITE_NAME
    url_pattern = scraping.HTTPS_PREFIX + r"skydemonorder\.com/projects/(?P<NovelID>[\w\d-]+)"
    title_selector = scraping.Selector("header > div > h1")
    status_map = {"complete": data.NovelStatus.COMPLETED, "ongoing": data.NovelStatus.ONGOING}

    extra_css = """\
    :root {
        --colors-primary-50: 255 255 255;
        --colors-primary-100: 239 239 239;
        --colors-primary-200: 208 208 208;
        --colors-primary-300: 192 192 192;
        --colors-primary-400: 115 115 115;
        --colors-primary-500: 82 82 82;
        --colors-primary-600: 55 55 55;
        --colors-primary-700: 23 23 23;
        --colors-primary-800: 15 15 15;
        --colors-highlight: 246 82 82;
        --colors-system: 236 0 155;
        --colors-novel-system-box-bg-1: 76 155 214;
        --colors-novel-system-box-bg-2: 217 246 252;
        --colors-novel-system-box-shadow: 15 104 160;
        --colors-novel-system-box-border: 15 104 160;
        --colors-tag-ongoing: 34 84 61;
        --colors-tag-complete: 44 82 130;
        --colors-tag-dropped: 116 42 42;
        --colors-tag-hiatus: 139 94 60;
    }

    .text-center {
        text-align: center !important;
    }

    .novel-system-box {
        --tw-border-opacity: 1;
        --tw-text-opacity: 1;
        background: linear-gradient(180deg,rgb(var(--colors-novel-system-box-bg-1)) 35%,rgb(var(--colors-novel-system-box-bg-2)) 214%);
        border-color: rgb(var(--colors-system)/var(--tw-border-opacity));
        border-width: 1px;
        border: 1px solid rgb(var(--colors-novel-system-box-border));
        color: rgb(var(--colors-system)/var(--tw-text-opacity));
        color: #fffffd;
        font-family: Rajdhani,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica Neue,Arial,Noto Sans,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol,Noto Color Emoji;
        font-family: Rajdhani,serif;
        font-weight: 500;
        margin: 0 auto;
        padding: 1rem;
        text-shadow: 1px 1px 2px rgb(var(--colors-novel-system-box-shadow)),0 0 1em rgb(var(--colors-novel-system-box-shadow)),0 0 .2em rgb(var(--colors-novel-system-box-shadow));
        unicode-range: u+263c-2653;
        width: -moz-fit-content;
        width: fit-content;

        /* new */
        margin-bottom: 1em !important;
    }
    """

    def get_novel_data_from_section(self, page: BeautifulSoup, pattern):
        """
        Fetch a list of chapters from a chapter section.

        :params page: The HTML tree of the page.
        :params pattern: A pattern to match against the section header. Only
                         returns results from matching sections.
        """
        pattern = re.compile(pattern, re.IGNORECASE)
        result = []

        for section in page.select("section"):
            header = section.find("h3")
            header_str = self._text(header)

            if not (match := pattern.match(header_str)):
                continue

            novel_data = None
            novel_data_raw = section.get("x-data")

            #
            # Handle Chapters as a List
            #
            # {
            #   expanded: 1,
            #   sortOrder: 'desc',
            #   chapters: (function(data) {
            #       if (!Array.isArray(data)) {
            #           data = Object.values(data);
            #       }
            #       return data;
            #   })([{"full_title":"Ep.19: Skill [...] "has_images":false}])
            # }
            #
            if match := re.search(r"\}\)\((\[.*\}\])\)\s*\}", novel_data_raw):
                novel_data_list = json.loads(match.group(1))
                novel_data = reversed(novel_data_list)

            #
            # Handle Chapters as a mapping (list index to chapter data)
            #
            # {
            #   expanded: 1,
            #   sortOrder: 'desc',
            #   chapters: (function(data) {
            #           if (!Array.isArray(data)) {
            #               data = Object.values(data);
            #           }
            #           return data;
            #   })({"19":{"full_title": [...] "is_mature":false,"has_images":false}})
            # }
            #
            if match := re.search(r"return data;\s*\}\)\((\{.*\}\})\)\s*\}", novel_data_raw):
                novel_data_map = json.loads(match.group(1))
                novel_data = [novel_data_map[str(key)] for key in reversed(list(map(int, novel_data_map.keys())))]

            if novel_data is None:
                logger.warn('Unable to extra chapter data from x-data="%s"', novel_data_raw)
                continue

            result.extend(novel_data)

        #
        # {
        #   "full_title": "Ep.1: The First Chapter",
        #   "slug": "name-of-chapter-slug",
        #   "project": {
        #       "slug": "name-of-novel-slug","
        #       "is_mature": false
        #   },
        #   "views":15182,
        #   "posted_at": "2021-12-11",
        #   "is_mature": false,
        #   "has_images": false
        # }
        #
        return result

    def get_status(self, page) -> data.NovelStatus:
        """Extract the novel's status from the page."""
        items = page.select("header > div > p > span")
        assert len(items) == 1
        item = items[0]
        return self.status_map.get(item.text.strip().lower(), data.NovelStatus.UNKNOWN)

    def get_author(self, page):
        """
        Return None since SkyDemonOrder doesn't list the author.

        Since they have a limited number of projects, I'll manually add some of
        the authors here.
        """
        title = self.get_title(page)
        return TITLE_AUTHOR_MAP.get(title)

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
            divs: list[Tag] = description.parent.find_all("div", recursive=False)
            for div in divs[1].find_all("div", recursive=False):
                name = div.find("strong").text.strip()
                value = div.find("span").text.strip()
                if name == "Views":
                    novel.extras["Views"] = f"{value} view(s) (as of {datetime.date.today():%Y-%m-%d})"
                if name == "Last Update":
                    novel.published_on = datetime.datetime.strptime(value, "%Y-%m-%d").date()

        # Note: Unlike some other sites on which author's self-publish or sites
        # that scrape content from the original sources, SkyDemonOrder is a translation
        # group, so we can just blindly set them as the translator for stories scraped
        # from their site.
        novel.translator = data.Person(name="SkyDemonOrder", url="https://skydemonorder.com/")

        #
        # The list of paid chapters has the "posted_at" date set to the date that
        # the chapter is scheduled to roll over from Paid-Only to Free, so by
        # scraping the Paid Episodes section we effectively get a tentative
        # release schedule for all episodes that have already been translated.
        #
        paid_chapters = self.get_novel_data_from_section(page, r"Paid\s+(Chapters|Episodes)")
        novel.extras["release_schedule"] = [
            {
                "title": chapter["full_title"],
                "release_date": self._date(chapter["posted_at"]),
                "url": urllib.parse.urljoin(base=url, url=f"/projects/{chapter['project']['slug']}/{chapter['slug']}"),
            }
            for chapter in paid_chapters
        ]

    def get_cover_image(self, page):
        """Get cover image url."""
        images = page.select("main img")
        assert len(images) == 1, "Expected to only find one <img> tag on novel page."
        image = images[0]
        return data.Image(url=image.get("src"))

    def get_chapters(self, page, url):
        """Return the list of chapters from the page."""
        chapters = []
        novel_data = self.get_novel_data_from_section(page, r"(Free\s+)?(Chapters|Episodes)")

        for idx, chapter in enumerate(novel_data):
            logger.debug("Chapter [%d] Data: %s", idx, chapter)
            url = urllib.parse.urljoin(base=url, url=f"/projects/{chapter['project']['slug']}/{chapter['slug']}")
            title = chapter["full_title"]
            pub_date = self._date(chapter["posted_at"])
            chapters.append(data.Chapter(chapter_no=idx, title=title, url=url, pub_date=pub_date))

        return chapters
