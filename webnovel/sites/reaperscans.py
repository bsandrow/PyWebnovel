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
        page_no = 1
        chapters = []
        while True:
            page_url = f"{url}?page={page_no}"
            page = self.get_page(page_url)
            chapter_batch = page.select(self.chapter_selector.paths[0])
            free_chapters = [ch for ch in chapter_batch if ch.select_one("a > div > div i.fa-coins") is None]

            print(f"{len(chapter_batch)} chapter(s) on page {page_no}")
            print(f"{len(free_chapters)} free chapter(s) on page {page_no}")

            if len(chapter_batch) == 0:
                break

            for chapter_li in free_chapters:
                chapter_url = chapter_li.select_one("a").get("href")
                chapter_title = chapter_li.select_one("a > div p").text.strip()
                chapter_no = None
                if match := re.match(r"Chapter (\d+)", chapter_title):
                    chapter_no = match.group(1)
                chapter = Chapter(url=chapter_url, title=chapter_title, chapter_no=chapter_no)
                chapters.append(chapter)

            page_no += 1

        return chapters
