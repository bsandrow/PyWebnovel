import datetime
from unittest import TestCase

from bs4 import BeautifulSoup
import requests_mock

from webnovel import data
from webnovel.sites import wuxiarealm

from ..helpers import get_test_data

NOVEL_URL = "https://wuxiarealm.com/novel/creepy-story-club/"
NOVEL_PAGE = get_test_data("wuxiarealm/novel.html")

NOVEL_JSON_URL = "https://wuxiarealm.com/wp-json/wp/v2/novel-series/27150"
NOVEL_JSON = get_test_data("wuxiarealm/novel.json")

GENRES_JSON_URL = "https://wuxiarealm.com/wp-json/wp/v2/genre?post=27150"
GENRES_JSON = get_test_data("wuxiarealm/genres.json")

CHAPTER_LIST_PAGE_1_URL = "https://wuxiarealm.com/wp-json/novel-id/v1/dapatkan_chapter_dengan_novel?category=27150&perpage=100&order=ASC&paged=1"
CHAPTER_LIST_PAGE_1 = get_test_data("wuxiarealm/chapter_list_p1.json")

CHAPTER_LIST_PAGE_2_URL = "https://wuxiarealm.com/wp-json/novel-id/v1/dapatkan_chapter_dengan_novel?category=27150&perpage=100&order=ASC&paged=2"
CHAPTER_LIST_PAGE_2 = get_test_data("wuxiarealm/chapter_list_p2.json")


req_mock = requests_mock.Mocker()
req_mock.get(NOVEL_URL, text=NOVEL_PAGE)
req_mock.get(NOVEL_JSON_URL, text=NOVEL_JSON)
req_mock.get(GENRES_JSON_URL, text=GENRES_JSON)
req_mock.get(CHAPTER_LIST_PAGE_1_URL, text=CHAPTER_LIST_PAGE_1)
req_mock.get(CHAPTER_LIST_PAGE_2_URL, text=CHAPTER_LIST_PAGE_2)


class WuxiaRealmNovelTestCase(TestCase):
    def setUp(self):
        req_mock.start()
        self.page = BeautifulSoup(NOVEL_PAGE, "html.parser")

    def tearDown(self):
        req_mock.stop()

    def test_get_status(self):
        scraper = wuxiarealm.WuxiaRealmScraper()
        actual = scraper.get_status(self.page)
        expected = data.NovelStatus.COMPLETED
        self.assertEqual(actual, expected)

    def test_get_summary(self):
        scraper = wuxiarealm.WuxiaRealmScraper()
        actual = scraper.get_summary(self.page)
        expected = next(
            BeautifulSoup(
                (
                    '<div id="editdescription">\n<p>Have you ever thought that the state of the world as it '
                    "presently is, could revert to the laws of the ancients? When a series of strange incidents"
                    " beginning with the disappearance of his friend led Luo Yuan to question the possibility "
                    "of an apocalypse, he becomes embroiled in the midst of a global-scale chaos.</p>\n<p>"
                    "Evolution has turned the flora and fauna of the vast and bountiful Earth into something "
                    "that had never been seen before. Coincidentally, the all-dominating Homo sapiens have "
                    "ended up at the bottom of the food chain. From mystery to crisis, will Luo Yuan discover "
                    "a means of saving humanity by racing to the top of the food chain? Or will he strive in "
                    "accordance with the law of the jungle? It is the dawn of an age of the survival of the "
                    "fittest.</p>\n</div>\n"
                ),
                "html.parser",
            ).children
        )
        self.assertEqual(actual, expected)

    def test_get_title(self):
        scraper = wuxiarealm.WuxiaRealmScraper()
        actual = scraper.get_title(self.page)
        expected = "Creepy Story Club"
        self.assertEqual(actual, expected)

    def test_get_cover_image(self):
        scraper = wuxiarealm.WuxiaRealmScraper()
        actual = scraper.get_cover_image(self.page)
        expected = data.Image(url="https://media.wuxiarealm.com/creepy-story-club.jpg")
        self.assertEqual(actual, expected)

    def test_get_genres(self):
        scraper = wuxiarealm.WuxiaRealmScraper()
        actual = scraper.get_genres(self.page)
        expected = [
            "Mystery",
            "Romance",
            "Mature",
            "Harem",
            "Supernatural",
            "Fantasy",
            "Action",
            "Martial Arts",
            "Adventure",
            "Sci-fi",
        ]
        self.assertEqual(set(actual), set(expected))

    def test_get_tags(self):
        scraper = wuxiarealm.WuxiaRealmScraper()
        actual = scraper.get_tags(self.page)
        expected = [
            "Evolution",
            "Military",
            "Determined Protagonist",
            "Cautious Protagonist",
            "Weak to Strong",
            "Post-apocalyptic",
            "Charismatic Protagonist",
            "Calm Protagonist",
            "Clever Protagonist",
            "Character Growth",
            "Beast Companions",
            "Firearms",
            "Gore",
            "Beautiful Female Lead",
            "Survival",
            "Loli",
            "Pragmatic Protagonist",
            "Apocalypse",
            "Dark",
            "Game Elements",
            "Mature Protagonist",
            "Monsters",
            "Pregnancy",
            "Sword Wielder",
            "Mutated Creatures",
            "Male Protagonist",
            "Aliens",
            "Mutations",
            "Level System",
            "Early Romance",
            "Threesome",
            "Modern Day",
            "Special Abilities",
            "Saving the World",
            "Overpowered Protagonist",
            "Polygamy",
            "Betrayal",
            "Monster Tamer",
            "Ruthless Protagonist",
            "Psychic Powers",
            "Handsome Male Lead",
            "Beasts",
            "Artifact Crafting",
            "God Protagonist",
            "Genetic Modifications",
        ]
        self.assertEqual(set(actual), set(expected))

    def test_scrape(self):
        scraper = wuxiarealm.WuxiaRealmScraper()
        actual = scraper.scrape(url=NOVEL_URL)
        expected = data.Novel(
            url=NOVEL_URL,
            novel_id="creepy-story-club",
            site_id="WuxiaRealm.com",
            title="Creepy Story Club",
            status=data.NovelStatus.COMPLETED,
            author=data.Person(name="Don", email=None, url=None),
            cover_image=data.Image(url="https://media.wuxiarealm.com/creepy-story-club.jpg"),
            summary=next(
                BeautifulSoup(
                    (
                        '<div id="editdescription">\n<p>Have you ever thought that the state of the world as it '
                        "presently is, could revert to the laws of the ancients? When a series of strange incidents"
                        " beginning with the disappearance of his friend led Luo Yuan to question the possibility "
                        "of an apocalypse, he becomes embroiled in the midst of a global-scale chaos.</p>\n<p>"
                        "Evolution has turned the flora and fauna of the vast and bountiful Earth into something "
                        "that had never been seen before. Coincidentally, the all-dominating Homo sapiens have "
                        "ended up at the bottom of the food chain. From mystery to crisis, will Luo Yuan discover "
                        "a means of saving humanity by racing to the top of the food chain? Or will he strive in "
                        "accordance with the law of the jungle? It is the dawn of an age of the survival of the "
                        "fittest.</p>\n</div>\n"
                    ),
                    "html.parser",
                ).children
            ),
            genres=[
                "Action",
                "Adventure",
                "Fantasy",
                "Harem",
                "Martial Arts",
                "Mature",
                "Mystery",
                "Romance",
                "Sci-fi",
                "Supernatural",
            ],
            tags=[
                "Aliens",
                "Apocalypse",
                "Artifact Crafting",
                "Beast Companions",
                "Beasts",
                "Beautiful Female Lead",
                "Betrayal",
                "Calm Protagonist",
                "Cautious Protagonist",
                "Character Growth",
                "Charismatic Protagonist",
                "Clever Protagonist",
                "Dark",
                "Determined Protagonist",
                "Early Romance",
                "Evolution",
                "Firearms",
                "Game Elements",
                "Genetic Modifications",
                "God Protagonist",
                "Gore",
                "Handsome Male Lead",
                "Level System",
                "Loli",
                "Male Protagonist",
                "Mature Protagonist",
                "Military",
                "Modern Day",
                "Monster Tamer",
                "Monsters",
                "Mutated Creatures",
                "Mutations",
                "Overpowered Protagonist",
                "Polygamy",
                "Post-apocalyptic",
                "Pragmatic Protagonist",
                "Pregnancy",
                "Psychic Powers",
                "Ruthless Protagonist",
                "Saving the World",
                "Special Abilities",
                "Survival",
                "Sword Wielder",
                "Threesome",
                "Weak to Strong",
            ],
            extras={"Added to Library Count": "1", "Country": "China", "View Count": "298 Views", "Year": "2016"},
            chapters=[
                data.Chapter(
                    url="https://wuxiarealm.com/creepy-story-club/chapter-1/",
                    chapter_no=0,
                    slug="chapter-1",
                    title="Chapter 1",
                    pub_date=datetime.datetime(2020, 11, 10, 8, 53, 14),
                ),
                data.Chapter(
                    url="https://wuxiarealm.com/creepy-story-club/chapter-2/",
                    chapter_no=1,
                    slug="chapter-2",
                    title="Chapter 2",
                    pub_date=datetime.datetime(2020, 11, 10, 8, 53, 18),
                ),
                data.Chapter(
                    url="https://wuxiarealm.com/creepy-story-club/chapter-3/",
                    chapter_no=2,
                    slug="chapter-3",
                    title="Chapter 3",
                    pub_date=datetime.datetime(2020, 11, 10, 8, 53, 21),
                ),
                data.Chapter(
                    url="https://wuxiarealm.com/creepy-story-club/chapter-4/",
                    chapter_no=3,
                    slug="chapter-4",
                    title="Chapter 4",
                    pub_date=datetime.datetime(2020, 11, 10, 8, 53, 24),
                ),
                data.Chapter(
                    url="https://wuxiarealm.com/creepy-story-club/chapter-5/",
                    chapter_no=4,
                    slug="chapter-5",
                    title="Chapter 5",
                    pub_date=datetime.datetime(2020, 11, 10, 8, 53, 28),
                ),
                data.Chapter(
                    url="https://wuxiarealm.com/creepy-story-club/chapter-6/",
                    chapter_no=5,
                    slug="chapter-6",
                    title="Chapter 6",
                    pub_date=datetime.datetime(2020, 11, 10, 8, 53, 31),
                ),
            ],
        )

        self.assertEqual(actual, expected)
