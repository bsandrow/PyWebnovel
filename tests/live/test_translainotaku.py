"""Live tests for TranslatinOtaku."""

import datetime
from unittest import TestCase, mock

import pytest

from webnovel import data
from webnovel.sites import translatinotaku

from ..helpers import WpMangaScraperTestCase

URL2 = "https://translatinotaku.net/novel/the-100th-regression-of-the-max-level-player/rmlp-chapter-1-the-midnight-bell-part-1/"


@pytest.mark.live
class NovelScraperTestCase(WpMangaScraperTestCase):
    novel_url = "https://translatinotaku.net/novel/the-100th-regression-of-the-max-level-player/"
    scraper_class = translatinotaku.NovelScraper
    expected_novel_id = "the-100th-regression-of-the-max-level-player"
    expected_synopsis = (
        '<div class="summary__content show-more">\n'
        "<p>Alternative Name: The Max-Level Player’s 100th Regression</p>\n"
        "<p>On the dawn of a fresh New Year, an ominous figure emerged, shrouded"
        " in a guise of an angel but harboring the malevolence of a devil. With a "
        "chilling voice, it proclaimed, [Every month, you humans will be thrust into"
        " a perilous quest. Your survival hinges on overcoming 20 grueling rounds.]"
        "</p>\n"
        "<p>Suddenly, I found myself ensnared in this dangerous survival game, a grotesque "
        "merry-go-round where every turn carried the stench of death. Yet, I was not without"
        " any defenses. I possessed an unusual power: the power to regress 100 times, a "
        "chance to rewrite my fate.</p>\n"
        "<p>I stand on the precipice of my final regression, and I swear, ‘This time, I will"
        " conquer it. I will emerge victorious.’</p>\n"
        "<p>I’m no longer the insignificant shuttle that I once was. Today, I shed my former "
        "self, the one who had reached the pinnacle of power. Today, I am reborn for the last "
        "time as Black Scythe, a rookie player, a novice that once again will be become the "
        "Grim Reaper!</p>\n"
        "<!-- WP Biographia v4.0.0 -->\n"
        "<!-- WP Biographia v4.0.0 -->\n"
        "<!-- AI CONTENT END 1 -->\n"
        "</div>"
    )
    expected_status_section = {
        "Rank": mock.ANY,  # this value frequently fluctuates
        "Rating": mock.ANY,  # this value frequently fluctuates
        "Alternative": "Alternative Name: The Max-Level Player’s 100th Regression",
        "Status": "OnGoing",
        "Genre(s)": "Action, Adventure, Drama, Fantasy, Korean, Martial Arts, Original, Supernatural",
    }
    expected_cover_image_url = "https://translatinotaku.net/wp-content/uploads/2023/04/xxlarge.webp"
    expected_status = data.NovelStatus.ONGOING
    expected_title = "The 100th Regression of the Max-Level Player"
    expected_genres = ["Action", "Adventure", "Drama", "Fantasy", "Korean", "Martial Arts", "Original", "Supernatural"]
    expected_chapters = [
        (
            "https://translatinotaku.net/novel/the-100th-regression-of-the-max-level-player/rmlp-chapter-1-the-midnight-bell-part-1/",
            "RMLP Chapter 1: The Midnight Bell (Part 1)",
            datetime.datetime(2023, 8, 23, 0, 0),
        ),
        (
            "https://translatinotaku.net/novel/the-100th-regression-of-the-max-level-player/rmlp-chapter-1-the-midnight-bell-part-2/",
            "RMLP Chapter 1: The Midnight Bell (Part 2)",
            datetime.datetime(2023, 8, 23, 0, 0),
        ),
        (
            "https://translatinotaku.net/novel/the-100th-regression-of-the-max-level-player/rmlp-chapter-2-hwang-yongmin-part-1/",
            "RMLP Chapter 2: Hwang Yongmin (Part 1)",
            datetime.datetime(2023, 8, 23, 0, 0),
        ),
        (
            "https://translatinotaku.net/novel/the-100th-regression-of-the-max-level-player/rmlp-chapter-2-hwang-yongmin-part-2/",
            "RMLP Chapter 2: Hwang Yongmin (Part 2)",
            datetime.datetime(2023, 8, 23, 0, 0),
        ),
        (
            "https://translatinotaku.net/novel/the-100th-regression-of-the-max-level-player/rmlp-chapter-3-character-creation-part-1/",
            "RMLP Chapter 3: Character Creation (Part 1)",
            datetime.datetime(2023, 8, 23, 0, 0),
        ),
        (
            "https://translatinotaku.net/novel/the-100th-regression-of-the-max-level-player/rmlp-chapter-3-character-creation-part-2/",
            "RMLP Chapter 3: Character Creation (Part 2)",
            datetime.datetime(2023, 8, 23, 0, 0),
        ),
    ]


@pytest.mark.live
class ChapterScraperTestCase(TestCase):
    def test_process_chapter(self):
        chapter = data.Chapter(url=URL2, title="Chapter 2")
        scraper = translatinotaku.ChapterScraper()
        scraper.process_chapter(chapter)

        # Make sure that we don't end up with nothing
        self.assertIsNotNone(chapter.original_html)
        self.assertIsNotNone(chapter.html)
        self.assertNotEqual(chapter.original_html, "")
        self.assertNotEqual(chapter.html, "")

        html_tree = chapter.generate_html()
        self.assertIsNotNone(html_tree)

        for selector in (
            ".chapter-warning",
            "#text-chapter-toolbar",
            "#wp-manga-current-chap",
        ):
            results = html_tree.select(selector)
            self.assertEqual(list(results), [], f"Expected to find no results for selector: {selector!r}")

        # Check if a known block of text that should be there exists in the
        # content.
        for excerpt in (
            "Humans all possess the innate desire to survive, and Ryu Min is no exception.",
            "“They’re trying to mess with us. A beautiful angel cosplayer will appear at any moment.”",
        ):
            self.assertIn(
                excerpt,
                chapter.original_html,
                (
                    f"Unable to find excerpt in original HTML:\n"
                    f"  Excerpt: {excerpt!r}\n"
                    f"\n  -----\n\n"
                    f"  Original HTML:\n"
                    f"{chapter.original_html!r}"
                ),
            )
            self.assertIn(
                excerpt,
                chapter.html,
                (
                    f"Unable to find excerpt in final HTML:\n"
                    f"  Excerpt: {excerpt!r}\n"
                    f"\n  -----\n\n"
                    f"  Final HTML:\n"
                    f"{chapter.html!r}"
                ),
            )
            self.assertIn(excerpt, chapter.html)
