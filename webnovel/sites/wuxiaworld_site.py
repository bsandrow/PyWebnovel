"""WuxiaWorld.site scrapers and utilities."""

import re

from webnovel.data import Chapter, NovelStatus
from webnovel.html import DEFAULT_FILTERS, ElementBlacklistFilter, HtmlFilter, remove_element
from webnovel.scraping import HTTPS_PREFIX, NovelScraper, Selector

NOVEL_URL_PATTERN = HTTPS_PREFIX + r"wuxiaworld\.site/novel/([\w-]+)/"


class SiteAdFilter(HtmlFilter):
    """
    Remove the 'Read Latest Chapters at {SITE}' banner inserted into the content.

    Don't need this in the middle of chapters. The site that this was scraped from will
    be in the title page of the ebook.
    """

    def filter(self, html_tree):
        """Iterate over all direct descendants looking for the banner."""
        for item in html_tree.find_all(recursive=False):
            if re.match(r"read\s*latest\s*chapters\s*at\s*wuxia\s*world", item.text, re.IGNORECASE):
                remove_element(item)


class WuxiaWorldDotSiteScraper(NovelScraper):
    """Scraper for WuxiaWorld.site."""

    site_name = "WuxiaWorld.site"
    title_selector = Selector("div.post-title > h1")
    summary_selector = Selector("div.description-summary > div.summary__content")
    status_selector = Selector("div.post-status > div:nth-child(2) > .summary-content")
    status_map = {"OnGoing": NovelStatus.ONGOING, "Ongoing": NovelStatus.ONGOING, "Completed": NovelStatus.COMPLETED}
    author_name_selector = Selector("div.author-content > a")
    author_url_selector = Selector("div.author-content > a", attribute="href")
    genre_selector = Selector("div.genres-content > a")
    cover_image_url_selector = Selector("div.summary_image img", attribute="data-src")

    # Notes:
    #   - Need to filter out .chapter-warning because some chapters have this above the content which means we grab that
    #     instead of the content. Doesn't show up all of the time. For example, saw it only on one chapter in a ~1200
    #     chapter novel, but it caused that chapter's content to only be the banner content.
    chapter_content_selector = Selector(
        "div.reading-content > input#wp-manga-current-chap > div:not(.chapter-warning, #text-chapter-toolbar)"
    )

    # Notes:
    #   - Didn't add <style> as a default blacklist filter, but there are <style> elements added in the middle of content
    #     for this site, and they are unnecessary. The added <style> elements are associated with the content that the
    #     SiteAdFilter is removing.
    chapter_content_filters = DEFAULT_FILTERS + [ElementBlacklistFilter("style"), SiteAdFilter()]

    @staticmethod
    def get_novel_id(url: str) -> str:
        """Return the id of the novel that WuxiaWorld.site uses."""
        match = re.match(NOVEL_URL_PATTERN, url)
        return match.group(1) if match else None

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate that a URL matches something that works for WuxiaWorld.site and the scraper should support."""
        return re.match(NOVEL_URL_PATTERN, url) is not None

    def get_status(self, page):
        """Return the status of the novel."""
        for item in page.select("div.post-status .summary-heading"):
            if item.text and item.text.strip().lower() == "status":
                content = item.parent.select_one("div.summary-content")
                if content:
                    return self.status_map.get(content.text.strip(), NovelStatus.UNKNOWN)
        return NovelStatus.UNKNOWN

    @staticmethod
    def get_novel_id(url: str) -> str:
        """Return the Novel ID for the novel."""
        match = re.match(NOVEL_URL_PATTERN, url)
        return match.group(1) if match is not None else None

    def chapter_extra_processing(self, chapter: Chapter) -> None:
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
        results = chapter.html_content.find_all(limit=1)
        if results:
            text = results[0].text.strip()
            if "\n" not in text and (match := re.match(r"(?:Chapter\s*)?(\d+)(?: -|:)? \w+.*", text)):
                chapter.title = Chapter.clean_title(match.group(0))
                remove_element(results[0])

        chapter.title = chapter.title.replace(" - : ", ": ")

    def get_chapters(self, page, url: str) -> list:
        """Return the list of Chapter instances for WuxiaWorld.site."""
        url = url if url.endswith("/") else f"{url}/"
        chapter_list_url = f"{url}ajax/chapters/"
        chapter_list_page = self.get_page(chapter_list_url, method="post")
        return [
            Chapter(
                url=chapter_li.select_one("a").get("href"),
                title=(title := Chapter.clean_title(chapter_li.select_one("a").text)),
                chapter_no=Chapter.extract_chapter_no(title),
            )
            for chapter_li in chapter_list_page.select("li.wp-manga-chapter")
        ]
