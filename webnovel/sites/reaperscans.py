import re

from webnovel.data import Chapter, NovelStatus
from webnovel.scraping import NovelScraper, Selector


def validate_url(url: str) -> bool:
    return re.match(r'https?://(www\.)?reaperscans\.com/novels/\d+-\w+', url) is not None


class ReaperScansScraper(NovelScraper):
    title_selector = Selector("MAIN > DIV:nth-child(2) > DIV > DIV:first-child H1")
    status_selector = Selector("MAIN > DIV:nth-child(2) > SECTION > DIV:first-child DL > DIV:nth-child(4) DD")
    summary_selector = Selector("MAIN > DIV:nth-child(2) > SECTION > DIV:first-child > DIV > P")
    chapter_selector = Selector("MAIN > DIV:nth-child(2) > DIV UL[role=\"list\"] LI")
    chapter_title_selector = Selector("ARTICLE > P:nth-child(7)")
    next_chapter_selector = Selector(
        "MAIN > DIV:nth-child(2) > NAV:nth-child(2) > DIV:nth-child(3) > A:nth-child(2)", attribute="href"
    )
    first_chapter_link = Selector(
        "MAIN > DIV:nth-child(2) > DIV > DIV:first-child > DIV A:first-child", attribute="href"
    )
    status_map = {
        "Ongoing": NovelStatus.ONGOING,
        # I haven't seen any with this on the site, so I'm only guessing that the status would be "Complete" when they
        # finish the novel.
        "Completed": NovelStatus.COMPLETED,
        "Dropped": NovelStatus.DROPPED,
        "On hold": NovelStatus.HIATUS
    }

    def get_genres(self, page):
        return []

    def get_author(self, page):
        # Note: The only place I can find the author on their page is in the cover image, which
        #       obviously isn't scrape-able.
        return None

    def get_chapters(self, page, url):
        chapters = []
        chapter_url = self.first_chapter_link.parse_one(page, use_attribute=True)

        while chapter_url:
            # print(f"Chapter URL: {chapter_url}")
            chapter_page = self.get_page(chapter_url)
            next_url = self.next_chapter_selector.parse_one(chapter_page, use_attribute=True)

            # If we hit a chapter that is not free, then we need to skip it and end the loop. Since the paid chapters
            # are always the most recent chapters, it means that there are no more chapters to scrape.
            #
            error_msg = chapter_page.select_one("DIV.mt-2.text-sm.text-red-700")
            is_paid = error_msg is not None and "You need to be logged in" in error_msg

            if not is_paid:
                title = self.chapter_title_selector.parse_one(chapter_page)
                chapter_no = None
                if title:
                    match = re.match(r"Chapter (\d+)", title)
                    chapter_no = match.group(1) if match else None
                chapter = Chapter(url=chapter_url, title=title, chapter_no=chapter_no)
                chapters.append(chapter)
            chapter_url = next_url

        return chapters
