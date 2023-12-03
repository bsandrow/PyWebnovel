"""NovelNext scrapers and utilities."""

from webnovel.scraping import HTTPS_PREFIX
from webnovel.sites import novelbin

SITE_NAME = "NovelNext.org"


class NovelNextScraper(novelbin.NovelScraper):
    """Novel Scraper for NovelNext.org."""

    site_name = SITE_NAME
    chapter_list_api_url = "https://novelnext.org/ajax/chapter-archive?novelId={novel_id}"
    url_pattern = HTTPS_PREFIX + r"novelnext\.org/novelnext/(?P<NovelID>[\w-]+)"


class NovelNextChapterScraper(novelbin.ChapterScraper):
    """Chapter Scraper for NovelNext.org."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"novelnext\.org/novelnext/(?P<NovelID>[\w\d-]+)/(?P<ChapterID>[\w\d-]+)"
