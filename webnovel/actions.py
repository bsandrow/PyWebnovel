"""Functions to perform actions pulling multiple components together."""

import datetime
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Optional, Type

from webnovel import epub, http, sites, utils
from webnovel.data import Image
from webnovel.logs import LogTimer
from webnovel.scraping import ScraperBase

logger = logging.getLogger(__name__)
timer = LogTimer(logger)


class ScraperCache:
    """
    A cache for instances of NovelScraper and/or ChapterScraper.

    Avoid creating a new scraper instance for each url to be processed.
    """

    def __init__(self):
        self.scraper_map: dict[Type[ScraperBase], ScraperBase] = {}
        self.http_client: http.HttpClient = http.get_client()

    def get_scraper(self, url: str) -> ScraperBase:
        """Return an instance of a NovelScraper/ChapterScraper class that supports the provided url."""
        scraper_class = sites.find_chapter_scraper(url)
        if not scraper_class:
            return None
        scraper = self.scraper_map.get(scraper_class)
        if not scraper:
            scraper = self.scraper_map[scraper_class] = scraper_class(http_client=self.http_client)
        return scraper


def create_epub(novel_url: str, filename: str = None, cover_image_url: str = None, chapter_limit: int = None) -> None:
    """Create an epub file for the URL pointing at a webnovel."""
    http_client = http.get_client()
    scraper_class = sites.find_scraper(novel_url)
    if scraper_class is None:
        raise RuntimeError(f"Found no scraper class for: {novel_url}")
    scraper = scraper_class(http_client=http_client)
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
            novel.cover_image.load(client=http_client)
            epub_pkg.add_image(image=novel.cover_image, content=novel.cover_image.data, is_cover_image=True)

        assert novel.chapters

        chapters = sorted(novel.chapters, key=lambda ch: int(ch.chapter_no))
        if chapter_limit:
            chapters = chapters[:chapter_limit]

        start = datetime.datetime.utcnow()
        for chapter in chapters:
            logger.info("Processing chapter: %s", chapter.title)

            ch_scraper_class = sites.find_chapter_scraper(chapter.url)
            if ch_scraper_class in ch_scrapers:
                ch_scraper = ch_scrapers[ch_scraper_class]
            else:
                ch_scraper = ch_scrapers[ch_scraper_class] = ch_scraper_class(http_client=http_client)

            ch_scraper.process_chapter(chapter)

            epub_pkg.add_chapter(chapter)
        end = datetime.datetime.utcnow()

        total_time = (end - start).total_seconds()
        time_per_chapter = float(total_time) / float(len(chapters))
        logger.info(
            "Averaged %.2f second(s) per chapter or %.2f chapter(s) per second.",
            time_per_chapter,
            1.0 / time_per_chapter,
        )

        epub_pkg.save()


def set_cover_image_for_epub(epub_file: str, cover_image_path: str) -> None:
    """
    Set the cover image for an existing .epub file.

    :param epub_file: Path to an existing .epub file.
    :param cover_image_path: Path to a local image file or a (http/https) URL to
        a remove image file to set as the new cover image.
    """
    epub_pkg = epub.EpubPackage.load(epub_file)

    if cover_image_path.lower().startswith("http:") or cover_image_path.lower().startswith("https:"):
        logger.debug("Cover image path is URL. Downloading cover image from URL.")
        cover_image = Image(url=cover_image_path)
        cover_image.load()
    else:
        cover_image_path: Path = Path(cover_image_path)
        if not cover_image_path.exists():
            raise OSError(f"File does not exist: {cover_image_path}")

        with cover_image_path.open("rb") as fh:
            imgdata = fh.read()

        cover_image = Image(
            url="",
            data=imgdata,
            mimetype=Image.get_mimetype_from_image_data(imgdata),
            did_load=True,
        )

    epub_pkg.add_image(image=cover_image, content=cover_image.data, is_cover_image=True)
    epub_pkg.save()


def rebuild(epub_file: str, reload_chapters: Optional[Iterable[str]] = None) -> None:
    """
    Force the Epub package to be rebuilt from the JSON file.

    This is useful to regenerate an epub after changes have been made to the
    code in webnovel.epub. For example, applying fixes to the xhtml templates.
    Rebuilding the file prevents the need to build a new epub from scratch
    (including all of the downloading / scraping of content).

    :param epub_file: The epub file to rebuild.
    :param reload_chapters: A list of chapter slugs.
    """
    logger.info("Rebuilding package: %s", epub_file)
    epub_pkg = epub.EpubPackage.load(epub_file)

    if reload_chapters:
        with timer("Reloading Chapters"):
            chapter_slug_map = {chapter.slug: chapter for chapter in epub_pkg.chapters.values()}
            scraper_cache = ScraperCache()

            for chapter_slug in set(reload_chapters):
                logger.info("Reloading chapter for slug '%s'", chapter_slug)
                chapter_slug = chapter_slug.strip()

                if chapter_slug not in chapter_slug_map:
                    logger.warning("Not a valid chapter (slug=%s). Skipping slug.", repr(chapter_slug))
                    continue

                chapter = chapter_slug_map[chapter_slug]
                scraper = scraper_cache.get_scraper(chapter.url)
                if scraper:
                    scraper.process_chapter(chapter)
                else:
                    logger.warning("Unable to find scraper for url: %s", chapter.url)

    epub_pkg.save()


def update(ebook: str) -> None:
    """Update ebook."""
    pass
