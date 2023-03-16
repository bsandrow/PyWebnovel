"""Command to create an epub file from a link to a webnovel."""

import argparse
import time

from webnovel import epub, sites


def get_cli_options():
    """Parse the CLI options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-u", "--novel-url", help="The URL of the novel. Only used on ")
    options = parser.parse_args()
    return options


def run():
    """Run the command."""
    options = get_cli_options()
    scraper_class = sites.find_scraper(options.novel_url)
    if scraper_class is None:
        raise RuntimeError(f"Found no scraper class for: {options.novel_url}")
    scraper = scraper_class()
    novel = scraper.scrape(options.novel_url)
    filename = f"{novel.title}.epub"

    epub_pkg = epub.EpubPackage(filename=filename, novel=novel)
    if novel.cover_image:
        epub_pkg.add_image(novel.cover_image, is_cover_image=True)

    assert novel.chapters
    # for chapter in chapters[:2]:
    for chapter in sorted(novel.chapters, key=lambda ch: int(ch.chapter_no)):
        print(f"Processing chapter: {chapter.title}")
        scraper.process_chapters(chapters=[chapter])
        time.sleep(5)
        epub_pkg.add_chapter(chapter)

    epub_pkg.save(filename)


if __name__ == "__main__":
    run()
