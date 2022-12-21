import re

from webnovel.scraping import NovelScraper, Selector


def validate_url(url: str) -> bool:
    return re.match(r'https?://(www\.)?reaperscans\.com/novels/\d+-\w+', url) is not None


class ReaperScansNovelScraper(NovelScraper):
    title_selector = Selector("html.dark.fontawesome-i2svg-active.fontawesome-i2svg-complete body.font-sans.antialiased.bg-black div.flex.flex-col.h-screen.justify-between main.mb-auto div.mx-auto.py-8.grid.max-w-3xl.grid-cols-1.gap-4.sm:px-6.lg:max-w-screen-2xl.lg:grid-flow-col-dense.lg:grid-cols-3 div.p-2.space-y-4.lg:col-span-2.lg:col-start-1.lg:p-0 div.mx-auto.container div.focus:outline-none.dark:bg-neutral-850.rounded div.p-4.lg:p-6 div.lg:flex div.flex.flex-col.w-full div.flex.justify-between.mt-4.lg:mt-0")

# def get_novel(url: str) -> Novel:
#     scraper = cloudscraper.create_scraper()
#     response = scraper.get(url)
#     print(response.text)
