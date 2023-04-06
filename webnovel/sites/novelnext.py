"""NovelNext scrapers and utilities."""

from webnovel.scraping import HTTPS_PREFIX
from webnovel.sites.novelbin import NovelBinChapterScraper, NovelBinScraper

SITE_NAME = "NovelNext.org"
NOVEL_URL_PATTERN = HTTPS_PREFIX + r"novelnext\.org/novelnext/(?P<NovelID>[\w-]+)"


class NovelNextScraper(NovelBinScraper):
    """Novel Scraper for NovelNext.org."""

    site_name = SITE_NAME
    chapter_list_api_url = "https://novelnext.org/ajax/chapter-archive?novelId={novel_id}"


class NovelNextChapterScraper(NovelBinChapterScraper):
    """Chapter Scraper for NovelNext.org."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"novelnext\.org/novelnext/(?P<NovelID>[\w\d-]+)/(?P<ChapterId>[\w\d-]+)"
