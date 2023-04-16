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
