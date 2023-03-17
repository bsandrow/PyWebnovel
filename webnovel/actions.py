"""Functions to perform actions pulling multiple components together."""

import random
import time

from webnovel import epub, sites, utils


def create_epub(novel_url: str, filename: str = None, chapter_limit: int = None) -> None:
    """Create an epub file for the URL pointing at a webnovel."""
    scraper_class = sites.find_scraper(novel_url)
    if scraper_class is None:
        raise RuntimeError(f"Found no scraper class for: {novel_url}")
    scraper = scraper_class()
    novel = scraper.scrape(novel_url)

    filename = utils.clean_filename(filename or f"{novel.title}.epub")
    print(f"Generating {filename}...")

    epub_pkg = epub.EpubPackage(filename=filename, novel=novel)
    if novel.cover_image:
        epub_pkg.add_image(novel.cover_image, is_cover_image=True, client=scraper.http_client)

    assert novel.chapters

    chapters = sorted(novel.chapters, key=lambda ch: int(ch.chapter_no))
    if chapter_limit:
        chapters = chapters[:chapter_limit]
    for index, chapter in enumerate(chapters, start=1):
        print(f"Processing chapter: {chapter.title}")
        scraper.process_chapters(chapters=[chapter])
        if index % 2 == 0:
            time.sleep(random.randint(3, 7))
        epub_pkg.add_chapter(chapter)

    epub_pkg.save(filename)
