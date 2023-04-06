"""Functions to perform actions pulling multiple components together."""

import logging
import time

from webnovel import epub, sites, utils
from webnovel.data import Image
from webnovel.epub.data import EpubOptions
from webnovel.logs import LogTimer

logger = logging.getLogger(__name__)
timer = LogTimer(logger)


def create_epub(novel_url: str, filename: str = None, cover_image_url: str = None, chapter_limit: int = None) -> None:
    """Create an epub file for the URL pointing at a webnovel."""
    scraper_class = sites.find_scraper(novel_url)
    if scraper_class is None:
        raise RuntimeError(f"Found no scraper class for: {novel_url}")
    scraper = scraper_class()
    novel = scraper.scrape(novel_url)
    logger.info(f"Found %d Chapter(s).", len(novel.chapters))

    if cover_image_url:
        novel.cover_image = Image(url=cover_image_url)

    filename = utils.clean_filename(filename or f"{novel.title}.epub")
    ch_scrapers = {}

    with timer("Generating %s", filename):
        epub_pkg = epub.EpubPackage(
            file_or_io=filename,
            metadata=novel,
            options={},
            extra_css=novel.extra_css,
        )

        if novel.cover_image:
            novel.cover_image.load(client=scraper.http_client)
            epub_pkg.add_image(image=novel.cover_image, content=novel.cover_image.data, is_cover_image=True)

        assert novel.chapters

        chapters = sorted(novel.chapters, key=lambda ch: int(ch.chapter_no))
        if chapter_limit:
            chapters = chapters[:chapter_limit]
        for chapter in chapters:
            logger.info(f"Processing chapter: {chapter.title}")
            ch_scraper_class = sites.find_chapter_scraper(chapter.url)
            if ch_scraper_class in ch_scrapers:
                ch_scraper = ch_scrapers[ch_scraper_class]
            else:
                ch_scraper = ch_scrapers[ch_scraper_class] = ch_scraper_class()
            ch_scraper.process_chapter(chapter)
            epub_pkg.add_chapter(chapter)

        epub_pkg.save()
