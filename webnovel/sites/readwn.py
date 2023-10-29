"""Scrapers for handling ReadWN.com Content."""

from webnovel import data, scraping

SITE_NAME = "ReadWN.com"


class ReadWnNovelScraper(scraping.NovelScraperBase):
    """Scraper for ReadWN.com Novels."""

    site_name = SITE_NAME
    url_pattern = scraping.HTTPS_PREFIX + r"(?:readwn|wuxiap).com/novel/(?P<NovelID>[\w\d-]+).html"
    status_map = {"completed": data.NovelStatus.COMPLETED, "ongoing": data.NovelStatus.ONGOING}

    def get_author(self, page):
        """Extract the novel's author."""
        author_block = page.select_one(".author [itemprop='author']")
        author_name = author_block.text.strip() if author_block else None
        return data.Person(name=author_name) if author_name else None

    def get_status(self, page):
        """Extract the novel's status."""
        header_stats = page.select_one(".header-stats")
        if header_stats:
            for header_stat in header_stats.find_all("span", recursive=False):
                stat_name = header_stat.find("small").text.strip()
                stat_value = header_stat.find("strong").text.strip().lower()
                if stat_name == "Status":
                    if stat_value in self.status_map:
                        return self.status_map[stat_value]
                    break
        return data.NovelStatus.UNKNOWN

    def get_title(self, page):
        """Extract the title from the page."""
        title_el = page.select_one(".main-head .novel-title")
        title_text = title_el.text.strip() if title_el else None
        return title_text

    def get_chapters(self, page, url):
        """Get the chapters."""
        page_no = 0
        novel_id = self.get_novel_id(url)

        def get(page_no: int, novel_id: str) -> list:
            api_url = (
                f"https://www.wuxiap.com/e/extend/fy.php?page={page_no}&wjm={novel_id}&X-Requested-With=XMLHttpRequest"
            )
            page = self.get_page(api_url)
