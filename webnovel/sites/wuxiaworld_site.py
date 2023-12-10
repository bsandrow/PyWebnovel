"""WuxiaWorld.site scrapers and utilities."""

import re

from bs4 import BeautifulSoup, Tag

from webnovel import html
from webnovel.data import Chapter, Image, NovelStatus
from webnovel.scraping import HTTPS_PREFIX, ChapterScraperBase, NovelScraperBase, Selector, WpMangaNovelInfoMixin

SITE_NAME = "WuxiaWorld.site"

EMOJI_REPLACE_MAP = {
    "https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/60/apple/81/black-diamond-suit_2666.png": "♦️",
    "https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/apple/237/black-spade-suit_2660.png": "♠",
    "https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/apple/237/black-club-suit_2663.png": "♣",
}


@html.register_html_filter(name="replace_card_suit_image")
def card_suit_image_replace(element: Tag) -> None:
    """Replace some image links to emojis that are failing with the unicode emoji instead."""
    for item in element.find_all("img"):
        src = item.get("src")
        replacement = EMOJI_REPLACE_MAP.get(src)
        if src and replacement:
            item.replace_with(BeautifulSoup(f"<span>{replacement}</span>", "html.parser").find("span"))


@html.register_html_filter(name="remove_site_ads.wuxiaworldsite")
def site_ads_filter(element: Tag) -> None:
    """
    Remove the 'Read Latest Chapters at {SITE}' banner inserted into the content.

    Don't need this in the middle of chapters. The site that this was scraped from will
    be in the title page of the ebook.

    Iterate over all direct descendants looking for the banner.
    """
    for item in element.find_all(recursive=False):
        if re.match(r"read\s*latest\s*chapters\s*at\s*wuxia\s*world", item.text, re.IGNORECASE):
            html.remove_element(item)


@html.register_html_filter(name="remove_style_elements.wuxiaworldsite")
def style_element_filter(element: Tag) -> None:
    """Remove <style> elements from content."""
    while element := element.find("style"):
        element.decompose()


class NovelScraper(WpMangaNovelInfoMixin, NovelScraperBase):
    """Scraper for WuxiaWorld.site."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"wuxiaworld\.site/novel/(?P<NovelID>[\w-]+)/"
    chapter_date_format = "%B %d, %Y"
    chapter_selector = ".wp-manga-chapter"


class ChapterScraper(ChapterScraperBase):
    """Scraper for WuxiaWorld.site chapter content."""

    site_name = SITE_NAME
    url_pattern = HTTPS_PREFIX + r"wuxiaworld\.site/novel/(?P<NovelID>[\w\d-]+)/(?P<ChapterID>[\w\d-]+)/?"

    # Notes:
    #   - Need to filter out .chapter-warning because some chapters have this
    #     above the content which means we grab that instead of the content.
    #     Doesn't show up all of the time. For example, saw it only on one
    #     chapter in a ~1200 chapter novel, but it caused that chapter's content
    #     to only be the banner content.
    #
    #   - The <input> is weird here. It's an unclosed <input> tag, and
    #     BeautifulSoup tries to close it by wrapping all of the sibling tag
    #     with an enclosing </input> tag.  The selector _should_ work without
    #     the "input >" in it, but just due to how BeautifulSoup parses the page
    #     we need to add this.
    #
    content_selector = Selector("div.reading-content > input > div:not(.chapter-warning, #text-chapter-toolbar)")

    # Notes:
    #   - Didn't add <style> as a default blacklist filter, but there are <style> elements added in the middle of content
    #     for this site, and they are unnecessary. The added <style> elements are associated with the content that the
    #     SiteAdFilter is removing.
    content_filters = ChapterScraperBase.content_filters + [
        "remove_style_elements.wuxiaworldsite",
        "remove_site_ads.wuxiaworldsite",
        "replace_card_suit_image",
    ]

    def post_process_content(self, chapter, content):
        """
        Deal with the weird/inconsitent way that chapter titles are added to chapter content.

        Sometimes it's in a <h3> at the top. Other times it's just in a <p>. Even within the same
        novel, the formatting differs from chapter to chapter. Even the chapter title content
        formatting (e.g. "Chapter 1 - Name" vs "Chapter 1: Name" vs "1 Name" etc)

        If the first element in the content matches somethings that looks like a chapter title,
        extract it, clean it up, replace Chapter.title and remove if from the chapter content. This
        prevents us from seeing the chapter title twice due to the way that we format the chapter
        xhtml files.
        """
        results = content.find("div").find_all(limit=1)
        candidate = results[0].text.strip() if results else ""
        if candidate and (match := Chapter.is_title_ish(candidate)):
            chapter.title = Chapter.clean_title(match.group(0))
            html.remove_element(results[0])
        chapter.title = chapter.title.replace(" - : ", ": ") if chapter.title else None
