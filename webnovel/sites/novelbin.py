import re

from webnovel.data import NovelStatus
from webnovel.scraping import NovelScraper, Selector


def validate_url(url: str) -> bool:
    return re.match(r'https?://(www\.)?novelbin\.net/n/\w+', url) is not None


class NovelBinScraper(NovelScraper):
    title_selector = Selector(".col-novel-main > .col-info-desc > .desc > .title")
    status_selector = Selector(".col-novel-main > .col-info-desc > .desc > .info-meta > li:nth-child(5) > a")
    status_map = {"Ongoing": NovelStatus.ONGOING, "Completed": NovelStatus.COMPLETED}
    genre_selector = Selector(".col-novel-main > .col-info-desc > .desc > .info-meta > li:nth-child(3) > a")
    author_name_selector = Selector(".col-novel-main > .col-info-desc > .desc > .info-meta > li:nth-child(2) > a")
    author_url_selector = Selector(".col-novel-main > .col-info-desc > .desc > .info-meta > li:nth-child(2) > a", attribute="href")
    summary_selector = Selector("div.tab-content div.desc-text")
