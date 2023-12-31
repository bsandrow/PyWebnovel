"""Functions to perform actions pulling multiple components together."""

import logging
import math
from pathlib import Path
from typing import Any, Iterable, Type
import urllib.parse

from webnovel import conf, epub, errors, events, http, sites, utils
from webnovel.data import Chapter, Image
from webnovel.logs import LogTimer
from webnovel.scraping import ScraperBase
from webnovel.utils import merge_dicts

logger = logging.getLogger(__name__)
timer = LogTimer(logger, log_level=logging.INFO)


def create_client(settings: conf.Settings = None):
    """
    Create an HttpClient instance.

    :params settings: A Settings instance to use when configuring the HttpClient.
    """
    settings = settings or conf.Settings()
    client = http.get_client(user_agent=settings.user_agent)
    if settings.cookies:
        for cname, cvalue in settings.cookies.items():
            client._session.cookies.set(cname, cvalue)


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

    client: http.HttpClient
    settings: conf.Settings

    def __init__(self, settings: conf.Settings = None):
        self.settings = settings or conf.Settings()
        self.client = create_client(self.settings)

    def __getattr__(self, name: str) -> Any:
        """Pull any attributes that don't exist on App from Settings."""
        return getattr(self.settings, name)

    def set_user_agent(self, user_agent_string: str) -> None:
        """Set the User-Agent header on the session."""
        self.client._session.headers["User-Agent"] = user_agent_string

    def set_cookie(self, cookie_name: str, cookie_value: str) -> None:
        """Set a cookie name/value pair on the current session."""
        self.client._session.cookies.set(cookie_name, cookie_value)

    def create_ebook(
        self,
        novel_url: str,
        filename: str = None,
        cover_image_url: str = None,
        chapter_limit: int = None,
        directory: str = ".",
    ) -> str:
        """
        Create an ebook for the URL pointing at a specific webnovel.

        :param novel_url: The URL of the webnovel to scrape.
        :param filename: (optional) The filename to use when saving the file.
            Defaults to using the title of the webnovel as the filename.
        :param cover_image_url: (optional) The URL of a cover image to use
            instead of the default cover image scraped from the novel page.
        :param chapter_limit: (optional) Limit the number of chapters to scrape.
            Leaving this blank scrapes all chapters.
        :param directory: (optional) The directory to create the ebook in.
            Defaults to the current directory.
        """
        scraper_class = sites.find_scraper(novel_url)
        if scraper_class is None:
            raise RuntimeError(f"Found no scraper class for: {novel_url}")
        scraper = scraper_class(http_client=self.client)
        novel = scraper.scrape(novel_url)
        logger.info(f"Found %d Chapter(s).", len(novel.chapters))
        events.trigger(
            events.Event.SCRAPE_TOTAL_CHAPTERS, context={"novel": novel, "total_chapters": len(novel.chapters)}
        )

        if cover_image_url:
            novel.cover_image = Image(url=cover_image_url)

        directory = Path(directory)
        filename = directory / utils.clean_filename(filename or f"{novel.title}.epub")

        events.trigger(
            event=events.Event.WN_CREATE_START,
            context={
                "path": filename,
                "novel_url": novel_url,
                "cover_image_url": cover_image_url,
                "scraper_class": scraper_class,
            },
            logger=logger,
        )

        with timer("Generating %s", filename):
            epub_pkg = epub.EpubPackage(
                file_or_io=filename,
                metadata=novel,
                options={},
                extra_css=novel.extra_css,
            )

            if novel.cover_image:
                novel.cover_image.url = urllib.parse.urljoin(base=novel_url, url=novel.cover_image.url)
                novel.cover_image.load(client=self.client)
                epub_pkg.add_image(image=novel.cover_image, content=novel.cover_image.data, is_cover_image=True)

            if novel.chapters:
                chapters = sorted(novel.chapters, key=lambda ch: int(ch.chapter_no))
                if chapter_limit:
                    chapters = chapters[:chapter_limit]
                self.add_chapters(ebook=epub_pkg, chapters=chapters)
            else:
                logger.warning("No chapters for novel.")

            epub_pkg.save()

            events.trigger(
                event=events.Event.WN_CREATE_END,
                context={
                    "path": filename,
                    "novel_url": novel_url,
                    "cover_image_url": cover_image_url,
                    "scraper_class": scraper_class,
                    "ebook": epub_pkg,
                },
                logger=logger,
            )

            return str(epub_pkg.filename)

    def add_chapters(self, ebook: epub.EpubPackage, chapters: list[Chapter], batch_size: int = 20) -> None:
        """
        Add a list of chapters to an ebook.

        Chapters are added in batches. At the end of each batch the ebook file
        is saved. If there is a failure, then everything up (and including) the
        last batch completed will be in the ebook.

        :param ebook: The ebook to add the chapters to.
        :param chapters: The list of chapters to add.
        :param batch_size: The size of the batches to add the chapters in.
        """
        total_time = 0
        scrapers = {}
        context = {"ebook": ebook, "chapters": chapters}
        total_batches = math.ceil(len(chapters) / batch_size)

        def get_chapter_scraper(url):
            chapter_scraper_class = sites.find_chapter_scraper(url)
            if chapter_scraper_class not in scrapers:
                scrapers[chapter_scraper_class] = chapter_scraper_class(http_client=self.client)
            return scrapers[chapter_scraper_class]

        events.trigger(events.Event.WN_FETCH_CHAPTERS_START, context, logger)
        for batch_no, batch in enumerate(utils.batcher_iter(chapters, batch_size=batch_size), start=1):
            batch_ctx = merge_dicts(
                context,
                {"total_batches": total_batches, "batch_no": batch_no, "batch_size": len(batch), "batch": batch},
            )

            with utils.Timer() as timer:
                events.trigger(events.Event.WN_CHAPTER_BATCH_START, batch_ctx, logger)
                for chapter in batch:
                    scraper = get_chapter_scraper(chapter.url)
                    scraper.process_chapter(chapter)
                    ebook.add_chapter(chapter)
                events.trigger(events.Event.WN_CHAPTER_BATCH_END, batch_ctx, logger)
            total_time += timer.time
            logger.debug("Saving chapters to ebook.")
            ebook.save()

        time_per_chapter = context["time_per_chapter"] = float(total_time) / float(len(chapters))
        events.trigger(events.Event.WN_FETCH_CHAPTERS_END, context, logger)

    def rebuild(self, epub_file: str, reload_chapters: Iterable[str] | None = None) -> None:
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
        else:
            with timer("Rebuilding Chapters"):
                for chapter in epub_pkg.chapters.values():
                    scraper_cls = sites.find_chapter_scraper(chapter.url)
                    if not scraper_cls:
                        raise Exception(f"Unable to find scraper for {chapter.url}")
                    scraper = scraper_cls(http_client=self.client)
                    scraper.post_processing(chapter)

        epub_pkg.save()

    def update(self, ebook: str, limit: int | None = None, ignore_path: str | Path | None = ".") -> int:
        """Update ebook."""
        ebook = Path(ebook)
        context = {"path": ebook}
        ignore_path = context["ignore_path"] = Path(ignore_path) if ignore_path else None
        events.trigger(event=events.Event.WN_UPDATE_START, context=context, logger=logger)

        pkg = context["pkg"] = epub.EpubPackage.load(ebook)

        novel_url = pkg.metadata.novel_url
        if not novel_url:
            raise ValueError(f"Unable to extract Novel URL from ebook: {ebook}")

        scraper_class = sites.find_scraper(novel_url)
        if not scraper_class:
            raise errors.NoMatchingNovelScraper(novel_url)

        scraper = scraper_class(http_client=self.client)
        novel = context["novel"] = scraper.scrape(novel_url)
        context["total"] = len(novel.chapters)
        events.trigger(event=events.Event.WN_UPDATE_CHAPTER_COUNT, context=context, logger=logger)

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
            urls = "\n".join(c.url for c in novel.chapters)
            print(f"\nURLS\n{urls}")
            raise errors.OrphanedUrlsError(orphaned_urls)

        #
        # Create a list of the missing chapters. If there are no missing chapters,
        # bail out with a log message as there is nothing to do here.
        #
        missing_chapters = [chapter for chapter in novel.chapters if chapter.url not in chapter_urls_in_file]
        if len(missing_chapters) < 1:
            context["new"] = 0
            events.trigger(event=events.Event.WN_UPDATE_NO_NEW_CHAPTERS, context=context, logger=logger)
            return 0

        #
        # Check that there are not out-of-order chapters popping up. We only want to
        # handle the case where the missing chapters come _after_ the pre-existing
        # chapters, sequentially.  Supporting filling in chapter gaps would have to
        # be for a future update (if support is ever added).
        #
        # existing_chapter_nos = set(ch.chapter_no for ch in pkg.chapters.values())
        # max_chapter_no = max(existing_chapter_nos)
        # non_sequential_chapters = [
        #     ch.url
        #     for ch in novel.chapters
        #     if ch.chapter_no not in existing_chapter_nos and ch.chapter_no < max_chapter_no
        # ]
        # if non_sequential_chapters:
        #     raise errors.NonsequentialChaptersError(non_sequential_chapters)

        # TODO make sure that the chapter_no values match up. Need to standardize
        #      handling of chapter_no across all scrapers to make sure this doesn't
        #      run into any snags.

        # TODO Fetch chapter content + add chapters to ebook + save ebook

        # TODO updated "last_updated_on" value

        if limit and len(missing_chapters) > limit:
            missing_chapters = missing_chapters[:limit]

        context["new"] = len(missing_chapters)
        events.trigger(event=events.Event.WN_UPDATE_NEW_CHAPTER_COUNT, context=context, logger=logger)

        self.add_chapters(ebook=pkg, chapters=missing_chapters, batch_size=20)
        pkg.save()
        return len(missing_chapters)

        # chapter_slug_map = {c.slug: c for c in pkg.chapters.values()}
        # raise NotImplementedError

    def info(self, ebook: str) -> None:
        """
        Return info on an ebook for display.

        :param ebook: Path to the ebook to display information about.
        """
        pkg = epub.EpubPackage.load(ebook)
        retval = {
            "Title": pkg.metadata.title,
            "Author": pkg.metadata.author.name if pkg.metadata.author else "",
            "Status": pkg.metadata.status.value if pkg.metadata.status else "",
            "Translator": pkg.metadata.translator.name if pkg.metadata.translator else "",
            "Genre(s)": ", ".join(map(repr, pkg.metadata.genres)) if pkg.metadata.genres else "",
            "Tag(s)": ", ".join(map(repr, pkg.metadata.tags)) if pkg.metadata.tags else "",
            "--": "--",
            "Novel URL": pkg.metadata.novel_url,
            "Cover Image URL": pkg.metadata.cover_image_url,
            "Site ID": pkg.metadata.site_id,
            "Novel ID": pkg.metadata.novel_id,
            "Source Published On": pkg.metadata.published_on.strftime("%Y-%m-%d") if pkg.metadata.published_on else "",
            "Source Last Updated On": (
                pkg.metadata.last_updated_on.strftime("%Y-%m-%d") if pkg.metadata.last_updated_on else ""
            ),
        }
        return retval

    def dir_update(self, directory: str) -> None:
        """Run the WebNovelDirectory command."""
        directory = Path(directory)
        from webnovel.dir import WNDController

        if directory.exists():
            wn_dir = WNDController.load(directory)
        else:
            wn_dir = WNDController.create(directory)

        logger.debug("Webnovel directory loaded.")

        if not wn_dir.validate():
            logger.error("Webnovel directory not valid.")
            return
        logger.debug("Webnovel directory validated.")
        wn_dir.update(self)
        wn_dir.save()

    def dir_clean(self, directory: str) -> None:
        """Run WNDController.clean()."""
        from webnovel.dir import WNDController

        wnd_ctrl = WNDController.from_path(directory)
        wnd_ctrl.clean()

    def dir_add(self, directory: str, epub_or_url: str) -> None:
        """Add a webnovel to directory."""
        directory = Path(directory)
        from webnovel.dir import WNDController

        if directory.exists():
            webnovel_directory = WNDController.load(directory)
        else:
            webnovel_directory = WNDController.create(directory)

        logger.debug("Webnovel directory loaded.")

        if not webnovel_directory.validate():
            logger.error("Webnovel directory not valid.")
            return
        logger.debug("Webnovel directory validated.")

        webnovel_directory.add(epub_or_url, self)
        webnovel_directory.save()


def set_cover_image_for_epub(filename: str, cover_image: str, settings: conf.Settings = None) -> None:
    """
    Set the cover image for an existing .epub file.

    :param filename: Path to the ebook to modify.
    :param cover_image: Local file path or HTTP URL to a cover image. This
        cover image will override the current cover image of the ebook.
    """
    epub_pkg = epub.EpubPackage.load(filename)
    client = create_client(settings)

    if cover_image.lower().startswith("http:") or cover_image.lower().startswith("https:"):
        logger.debug("Cover image path is URL. Downloading cover image from URL.")
        image = Image(url=cover_image)
        image.load(client=client)
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


def set_title_for_epub(filename: str, new_title: str) -> None:
    """
    Set the title of an .epub package.

    :param filename: Path to the epub file.
    :param new_title: The new value to set the title to.
    """
    epub_pkg = epub.EpubPackage.load(filename)
    old_title = epub_pkg.metadata.title
    epub_pkg.metadata.title = new_title
    epub_pkg.update_change_log(
        message=f"Changed title from '{old_title}' to '{new_title}'",
        old_value=old_title,
        new_value=new_title,
    )
    epub_pkg.save()
