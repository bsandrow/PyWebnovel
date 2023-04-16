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


class App:
    """Central Application for PyWebnovel."""

    debug: bool = False
    format: str = "epub"
    client: http.HttpClient

    def __init__(self, debug: bool = False, format: str = "epub"):
        self.debug = debug
        self.format = format
        self.client = http.get_client()

    def set_user_agent(self, user_agent_string: str) -> None:
        """Set the User-Agent header on the session."""
        self.client._session.headers["User-Agent"] = user_agent_string

    def set_cookie(self, cookie_name: str, cookie_value: str) -> None:
        """Set a cookie name/value pair on the current session."""
        self.client._session.cookies.set(cookie_name, cookie_value)

    def create_epub(
        self, novel_url: str, filename: str = None, cover_image_url: str = None, chapter_limit: int = None
    ) -> None:
        """
        Create an EPUB for the URL pointing at a specific webnovel.

        :param novel_url: The URL of the webnovel to scrape.
        :param filename: (optional) The filename to use when saving the file.
            Defaults to using the title of the webnovel as the filename.
        :param cover_image_url: (optional) The URL of a cover image to use
            instead of the default cover image scraped from the novel page.
        :param chapter_limit: (optional) Limit the number of chapters to scrape.
            Leaving this blank scrapes all chapters.
        """
        scraper_class = sites.find_scraper(novel_url)
        if scraper_class is None:
            raise RuntimeError(f"Found no scraper class for: {novel_url}")
        scraper = scraper_class(http_client=self.client)
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

    def set_cover_image_for_epub(self, filename: str, cover_image: str) -> None:
        """
        Set the cover image for an existing .epub file.

        :param filename: Path to the ebook to modify.
        :param cover_image: Local file path or HTTP URL to a cover image. This
            cover image will override the current cover image of the ebook.
        """
        epub_pkg = epub.EpubPackage.load(filename)

        if cover_image.lower().startswith("http:") or cover_image.lower().startswith("https:"):
            logger.debug("Cover image path is URL. Downloading cover image from URL.")
            image = Image(url=cover_image)
            image.load(client=self.client)
        else:
            cover_image: Path = Path(cover_image)
            if not cover_image.exists():
                raise OSError(f"File does not exist: {cover_image}")

            with cover_image.open("rb") as fh:
                imgdata = fh.read()

            image = Image(
                url="",
                data=imgdata,
                mimetype=Image.get_mimetype_from_image_data(imgdata),
                did_load=True,
            )

        epub_pkg.add_image(image=image, content=image.data, is_cover_image=True)
        epub_pkg.save()

    def rebuild(self, epub_file: str, reload_chapters: Optional[Iterable[str]] = None) -> None:
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

                for chapter_slug in set(reload_chapters):
                    logger.info("Reloading chapter for slug '%s'", chapter_slug)
                    chapter_slug = chapter_slug.strip()

                    if chapter_slug not in chapter_slug_map:
                        logger.warning("Not a valid chapter (slug=%s). Skipping slug.", repr(chapter_slug))
                        continue

                    chapter = chapter_slug_map[chapter_slug]
                    scraper_cls = sites.find_chapter_scraper(chapter.url)
                    if scraper_cls:
                        scraper = scraper_cls(http_client=self.client)
                        scraper.process_chapter(chapter)
                    else:
                        logger.warning("Unable to find scraper for url: %s", chapter.url)

        epub_pkg.save()

    def update(self, ebook: str) -> None:
        """Update ebook."""
        logger.info("Updating package: %s", ebook)
        pkg = epub.EpubPackage.load(ebook)

        novel_url = pkg.metadata.novel_url
        if not novel_url:
            raise ValueError(f"Unable to extract Novel URL from ebook: {ebook}")

        scraper_class = sites.find_scraper(novel_url)
        if not scraper_class:
            raise ValueError(f"Unable to find novel scraper for URL: {novel_url}")

        scraper = scraper_class(http_client=self.client)
        novel = scraper.scrape(novel_url)

        chapter_urls_in_file = set(pkg.chapters.keys())
        chapter_urls_fetched = {c.url for c in novel.chapters}

        #
        # Bail out if there are chapters in the file that do not match the fetched
        # chapter list.  This will need to be handled at some point in the future,
        # as one of the causes is an author pulling chapters from the site. In this
        # case, ignoring the orphaned chapters is something that the user may want
        # to do. If this is supported in the future, it might be required to only be
        # supported on a per scraper basis, as some sites don't provide enough
        # information to make this work correctly. Another cause, is that the site
        # goes through a revamp and the chapter url format has changed. In this
        # case, ignoring the orphans would basically screw up the whole ebook
        # with duplicate chapters. For now, the safest way to handle this is bail
        # out with an error, and in the future _maybe_ supporting the ability to
        # proceed even with orphans.
        #
        orphaned_urls = chapter_urls_in_file - chapter_urls_fetched
        if orphaned_urls:
            raise ValueError(
                f"Found chapter urls in file that are missing from the fetched chapter list: {orphaned_urls}"
            )

        #
        # Create a list of the missing chapters. If there are no missing chapters,
        # bail out with a log message as there is nothing to do here.
        #
        missing_chapters = [chapter for chapter in novel.chapters if chapter.url not in chapter_urls_in_file]
        if len(missing_chapters) < 1:
            logger.info("No new chapters found.")
            return

        #
        # Check that there are not out-of-order chapters popping up. We only want to
        # handle the case where the missing chapters come _after_ the pre-existing
        # chapters, sequentially.  Supporting filling in chapter gaps would have to
        # be for a future update (if support is ever added).
        #
        max_chapter_no = max(ch.chapter_no for ch in pkg.chapters.values())
        non_sequential_chapters = [ch.title or ch.url for ch in novel.chapters if ch.chapter_no < max_chapter_no]
        if non_sequential_chapters:
            raise ValueError(
                f"Found missing chapters ({non_sequential_chapters}) that don't come after the most "
                f"recent chapters in the ebook. PyWebnovel currently does not support filling in gaps "
                f"between chapters or handling the author going back to add a chapter in "
                f"the middle of previous chapters. (Note: this may change in the future though)"
            )

        # TODO make sure that the chapter_no values match up. Need to standardize
        #      handling of chapter_no across all scrapers to make sure this doesn't
        #      run into any snags.

        # TODO Fetch chapter content + add chapters to ebook + save ebook

        # TODO updated "last_updated_on" value

        chapter_slug_map = {c.slug: c for c in pkg.chapters.values()}
        raise NotImplementedError
