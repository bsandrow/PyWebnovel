import re

from webnovel.data import NovelStatus, Chapter
from webnovel.scraping import NovelScraper, Selector, HTTPS_PREFIX

NOVEL_URL_PATTERN = HTTPS_PREFIX + r"novelbin\.net/n/([\w-]+)"


def validate_url(url: str) -> bool:
    return re.match(NOVEL_URL_PATTERN, url) is not None


class NovelBinScraper(NovelScraper):
    title_selector = Selector(".col-novel-main > .col-info-desc > .desc > .title")
    status_selector = Selector(".col-novel-main > .col-info-desc > .desc > .info-meta > li:nth-child(5) > a")
    status_map = {"Ongoing": NovelStatus.ONGOING, "Completed": NovelStatus.COMPLETED}
    genre_selector = Selector(".col-novel-main > .col-info-desc > .desc > .info-meta > li:nth-child(3) > a")
    author_name_selector = Selector(".col-novel-main > .col-info-desc > .desc > .info-meta > li:nth-child(2) > a")
    author_url_selector = Selector(".col-novel-main > .col-info-desc > .desc > .info-meta > li:nth-child(2) > a", attribute="href")
    summary_selector = Selector("div.tab-content div.desc-text")

    @staticmethod
    def get_novel_id(url: str) -> str:
        match = re.match(NOVEL_URL_PATTERN, url)
        return match.group(1) if match is not None else None

    def get_chapters(self, page, url: str) -> list:
        novel_id = self.get_novel_id(url)
        print(f"URL: {url}")
        print(f"NOVEL ID: {novel_id}")
        page = self.get_page(f"https://novelbin.net/ajax/chapter-archive?novelId={novel_id}")

        def get_chapter_no(title: str):
            match = re.match(r"^\s*Chapter\s*(\d+)\. ", title, re.IGNORECASE)
            return match.group(1) if match is not None else None

        return [
            Chapter(
                url=chapter_li.select_one("A").get("href"),
                title=chapter_li.select_one("A").get("title"),
                chapter_no=get_chapter_no(chapter_li.select_one("A").get("title")),
            )
            for chapter_li in page.select("UL.list-chapter > LI")
        ]
