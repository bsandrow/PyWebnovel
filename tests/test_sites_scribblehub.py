import datetime
from unittest import TestCase, mock

from bs4 import BeautifulSoup
from freezegun import freeze_time
import requests_mock

from webnovel import data
from webnovel.sites import scribblehub

from .helpers import get_test_data

NOVEL_URL = "https://www.scribblehub.com/series/123456/creepy-story-club/"
NOVEL_PAGE = get_test_data("scribblehub/novel.html")

ADMIN_AJAX_URL = "https://www.scribblehub.com/wp-admin/admin-ajax.php"
ADMIN_AJAX_PAGE = get_test_data("scribblehub/admin-ajax.html")

CHAPTER_URL = "https://www.scribblehub.com/read/123456-creepy-story-club/chapter/54321/"
CHAPTER_PAGE = get_test_data("scribblehub/chapter.html")


class ScribbleHubNovelTestCase(TestCase):
    def test_get_status_ongoing(self):
        page = BeautifulSoup(NOVEL_PAGE, "html.parser")
        scraper = scribblehub.ScribbleHubScraper()
        actual = scraper.get_status(page)
        expected = data.NovelStatus.ONGOING
        self.assertEqual(actual, expected)

    def test_get_status_completed(self):
        page = BeautifulSoup(NOVEL_PAGE.replace("Ongoing", "Completed"), "html.parser")
        scraper = scribblehub.ScribbleHubScraper()
        actual = scraper.get_status(page)
        expected = data.NovelStatus.COMPLETED
        self.assertEqual(actual, expected)

    def test_get_status_hiatus(self):
        page = BeautifulSoup(NOVEL_PAGE.replace("Ongoing", "Hiatus"), "html.parser")
        scraper = scribblehub.ScribbleHubScraper()
        actual = scraper.get_status(page)
        expected = data.NovelStatus.HIATUS
        self.assertEqual(actual, expected)

    def test_get_status_unknown(self):
        page = BeautifulSoup(NOVEL_PAGE.replace("Ongoing", "ERROR"), "html.parser")
        scraper = scribblehub.ScribbleHubScraper()
        actual = scraper.get_status(page)
        expected = data.NovelStatus.UNKNOWN
        self.assertEqual(actual, expected)

    def test_get_title(self):
        page = BeautifulSoup(NOVEL_PAGE, "html.parser")
        scraper = scribblehub.ScribbleHubScraper()
        actual = scraper.get_title(page)
        expected = "Creepy Story Club"
        self.assertEqual(actual, expected)

    def test_get_tags(self):
        page = BeautifulSoup(NOVEL_PAGE, "html.parser")
        scraper = scribblehub.ScribbleHubScraper()
        actual = scraper.get_tags(page)
        expected = [
            "Adventurers",
            "Beastkin",
            "Beautiful Female Lead",
            "Bisexual Protagonist",
            "Character Growth",
            "Demons",
            "Dragons",
            "Dungeons",
            "Elves",
            "Female Protagonist",
            "Girl's Love Subplot",
            "Half-human Protagonist",
            "Human-Nonhuman Relationship",
            "Male to Female",
            "Monsters",
            "Parallel Worlds",
            "Reincarnation",
            "Sword Wielder",
            "Transported into Another World",
            "Weak to Strong",
        ]
        self.assertEqual(set(actual), set(expected))

    def test_get_genres(self):
        page = BeautifulSoup(NOVEL_PAGE, "html.parser")
        scraper = scribblehub.ScribbleHubScraper()
        actual = scraper.get_genres(page)
        expected = ["Action", "Adventure", "Fantasy", "Gender Bender", "Harem", "Isekai", "LitRPG", "Romance", "Smut"]
        self.assertEqual(set(actual), set(expected))

    def test_get_author(self):
        page = BeautifulSoup(NOVEL_PAGE, "html.parser")
        scraper = scribblehub.ScribbleHubScraper()
        actual = scraper.get_author(page)
        expected = data.Person(name="EnroItzal", url="https://www.scribblehub.com/profile/7964/enroitzal/")
        self.assertEqual(actual, expected)

    def test_scrape(self):
        with requests_mock.Mocker() as m, freeze_time("2022-01-01"):
            m.get(NOVEL_URL, text=NOVEL_PAGE)
            m.post(ADMIN_AJAX_URL, text=ADMIN_AJAX_PAGE)
            scraper = scribblehub.ScribbleHubScraper()
            actual = scraper.scrape(NOVEL_URL)
            expected = data.Novel(
                url=NOVEL_URL,
                novel_id="123456",
                site_id="ScribbleHub.com",
                title="Creepy Story Club",
                status=data.NovelStatus.ONGOING,
                summary=list(
                    BeautifulSoup(
                        '<div class="wi_fic_desc" property="description">'
                        "<p>Argon Raze, the best swordsman of the continent. He was dubbed the Sword Saint due to his unparalleled "
                        "skills with the sword. He lived a life of endless victories in duels and challenges. However, all that came "
                        "to an end when he challenged a young mage. He lost his winning streak and his life at the hands of this "
                        "young mage.<br />\n"
                        "Seemingly ready to accept his death, he found himself inside an unknown forest after being swallowed by "
                        "an immense light. He was still alive, he realized. Although, he also realized he wasn't the same Argon "
                        "Raze as before.</p>\n<p>Feel free to support me on Paypal or Patreon with five or more chapters ahead."
                        "</p>\n<p>P.S. Cover image is not mine. Credits to scottie_(phantom2) Feel free to pm me if the they wish "
                        "for it to be taken down.</p>\n<p>P.P.S. Update is on every Wednesday and Saturday 11a.m. PST</p>\n</div>",
                        "html.parser",
                    ).children
                )[0],
                genres=[
                    "Action",
                    "Adventure",
                    "Fantasy",
                    "Gender Bender",
                    "Harem",
                    "Isekai",
                    "LitRPG",
                    "Romance",
                    "Smut",
                ],
                tags=[
                    "Adventurers",
                    "Beastkin",
                    "Beautiful Female Lead",
                    "Bisexual Protagonist",
                    "Character Growth",
                    "Demons",
                    "Dragons",
                    "Dungeons",
                    "Elves",
                    "Female Protagonist",
                    "Girl's Love Subplot",
                    "Half-human Protagonist",
                    "Human-Nonhuman Relationship",
                    "Male to Female",
                    "Monsters",
                    "Parallel Worlds",
                    "Reincarnation",
                    "Sword Wielder",
                    "Transported into Another World",
                    "Weak to Strong",
                ],
                author=data.Person(name="EnroItzal", url="https://www.scribblehub.com/profile/7964/enroitzal/"),
                chapters=mock.ANY,
                cover_image=data.Image(
                    url="https://cdn.scribblehub.com/images/8/creepy-story-club_123456_1644057047.jpg"
                ),
                extras={
                    "Content Warning": ["Gore", "Sexual Content", "Strong Language"],
                    "Rankings": ["Ranked #1 in Sword Wielder"],
                    "User Stats": ["5528 reading", "548 plan to read", "78 completed", "200 paused", "213 dropped"],
                    "Views": "2.48M Views (as of 2022-Jan-01)",
                    "Favourites": "36150 Favorites (as of 2022-Jan-01)",
                    "Chapters per Week": "1 Chapters/Week (as of 2022-Jan-01)",
                    "Readers": "6567 Readers (as of 2022-Jan-01)",
                },
                published_on=datetime.datetime(2020, 8, 24, 0, 0),
                last_updated_on=datetime.datetime(2022, 11, 19, 18, 0),
            )
            self.assertEqual(actual, expected)


class ScribbleHubChapterTestCase(TestCase):
    maxDiff = None

    def test_scrape(self):
        with requests_mock.Mocker() as m:
            m.get(CHAPTER_URL, text=CHAPTER_PAGE)
            chapter = data.Chapter(url=CHAPTER_URL)
            scraper = scribblehub.ScribbleHubChapterScraper()

            self.assertEqual(
                chapter.to_dict(),
                {
                    "url": CHAPTER_URL,
                    "chapter_no": None,
                    "slug": None,
                    "html": None,
                    "title": None,
                    "pub_date": None,
                },
            )

            scraper.process_chapter(chapter)

            self.assertEqual(
                chapter.to_dict(),
                {
                    "url": CHAPTER_URL,
                    "chapter_no": None,
                    "slug": None,
                    "html": (
                        '<div class="chp_raw" id="chp_raw"><div class="pywn_authorsnotes"> '
                        '<div class="pywn_authorsnotes-title">-- Author\'s Note ---</div> '
                        '<div class="pywn_authorsnotes-body"><div '
                        'class="wi_authornotes_body">\n'
                        "\n"
                        "    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
                        "eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim "
                        "ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut "
                        "aliquip ex ea commodo consequat. Duis aute irure dolor in "
                        "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
                        "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
                        "culpa qui officia deserunt mollit anim id est "
                        "laborum.</div></div></div>\n"
                        "\n"
                        "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
                        "eiusmod tempor incididunt ut labore et dolore magna aliqua. Neque "
                        "aliquam vestibulum morbi blandit cursus. Phasellus vestibulum lorem "
                        "sed risus ultricies tristique nulla. Amet mattis vulputate enim "
                        "nulla. Morbi tristique senectus et netus et malesuada fames ac "
                        "turpis. Fames ac turpis egestas sed tempus. Eu sem integer vitae "
                        "justo eget magna fermentum. Quisque non tellus orci ac. Ac felis "
                        "donec et odio pellentesque diam volutpat commodo sed. Sed enim ut "
                        "sem viverra. At in tellus integer feugiat scelerisque varius "
                        "morbi.</p>\n"
                        "<p>Rhoncus aenean vel elit scelerisque mauris. Ac feugiat sed lectus "
                        "vestibulum mattis ullamcorper velit sed ullamcorper. Aliquet lectus "
                        "proin nibh nisl condimentum id. Ipsum dolor sit amet consectetur "
                        "adipiscing elit ut aliquam. Laoreet sit amet cursus sit amet. Enim "
                        "ut tellus elementum sagittis vitae et. Velit aliquet sagittis id "
                        "consectetur purus ut. Sit amet aliquam id diam maecenas ultricies mi "
                        "eget mauris. Proin nibh nisl condimentum id venenatis a. Velit "
                        "laoreet id donec ultrices tincidunt arcu non sodales. Lectus mauris "
                        "ultrices eros in cursus turpis. Est ante in nibh mauris cursus "
                        "mattis molestie. Nascetur ridiculus mus mauris vitae ultricies leo "
                        "integer. Vestibulum rhoncus est pellentesque elit. Ac turpis egestas "
                        "sed tempus urna. Sed viverra tellus in hac habitasse. Leo vel "
                        "fringilla est ullamcorper eget nulla facilisi.</p>\n"
                        '<div class="tbl_of">\n'
                        "\n"
                        "</div>\n"
                        "<p>Morbi tristique senectus et netus et malesuada fames ac. Nulla "
                        "facilisi nullam vehicula ipsum a arcu. Aliquet risus feugiat in ante "
                        "metus dictum at. Semper quis lectus nulla at volutpat diam ut. Quis "
                        "blandit turpis cursus in hac habitasse platea. Leo a diam "
                        "sollicitudin tempor. Erat imperdiet sed euismod nisi porta lorem "
                        "mollis aliquam ut. Ac ut consequat semper viverra nam libero justo "
                        "laoreet. Vestibulum lorem sed risus ultricies tristique nulla. Vel "
                        "quam elementum pulvinar etiam.</p>\n"
                        "<p>Nulla pellentesque dignissim enim sit amet. Amet consectetur "
                        "adipiscing elit ut. Ut porttitor leo a diam sollicitudin tempor. "
                        "Egestas sed sed risus pretium quam. Condimentum lacinia quis vel "
                        "eros donec ac odio tempor. Auctor eu augue ut lectus arcu bibendum "
                        "at varius vel. Egestas pretium aenean pharetra magna ac placerat "
                        "vestibulum lectus. Ut porttitor leo a diam. Amet nisl suscipit "
                        "adipiscing bibendum est ultricies integer quis. Porttitor lacus "
                        "luctus accumsan tortor posuere. Velit sed ullamcorper morbi "
                        "tincidunt ornare massa eget.</p>\n"
                        "<p>Blandit cursus risus at ultrices. Amet aliquam id diam maecenas "
                        "ultricies mi eget mauris. A lacus vestibulum sed arcu non odio "
                        "euismod lacinia at. Feugiat pretium nibh ipsum consequat nisl vel "
                        "pretium. Turpis egestas pretium aenean pharetra magna ac placerat. "
                        "Ultrices mi tempus imperdiet nulla malesuada pellentesque. Libero "
                        "justo laoreet sit amet cursus. Vulputate mi sit amet mauris commodo. "
                        "Vitae purus faucibus ornare suspendisse sed. Lectus nulla at "
                        "volutpat diam. Donec enim diam vulputate ut pharetra.</p>\n"
                        "</div>"
                    ),
                    "title": None,
                    "pub_date": None,
                },
            )
