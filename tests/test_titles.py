from unittest import TestCase

from webnovel import data

from .helpers import get_test_data

TEST_CASES = [
    ("Chapter 901:  901 Out of Control", "Chapter 901: Out of Control"),
    ("Chapter 100: 100 The Black Dragon", "Chapter 100: The Black Dragon"),
    # --
    ("Chapter Ch 102", "Chapter 102"),
    # --
    ("Chapter 761: Chapter 761", "Chapter 761"),
    ("Chapter 761: Chapter 761 No Openings", "Chapter 761: No Openings"),
    ("Chapter 761: Chapter 761: No Openings", "Chapter 761: No Openings"),
    ("Side Story 5: Side Story 5", "Side Story 5"),
    ("Side Story 5: Side Story 5 No Openings", "Side Story 5: No Openings"),
    ("Side Story 5: Side Story 5: No Openings", "Side Story 5: No Openings"),
    ("SS 5: SS 5", "SS 5"),
    ("SS 5: SS 5 No Openings", "SS 5: No Openings"),
    ("SS 5: SS 5: No Openings", "SS 5: No Openings"),
    # --
    ("Chapter 761: - No Openings", "Chapter 761: No Openings"),
    # --
    ("Chapter 100 - The Black Dragon", "Chapter 100: The Black Dragon"),
    ("Chapter 100  - The Black Dragon", "Chapter 100: The Black Dragon"),
    ("Chapter 100. The Black Dragon", "Chapter 100: The Black Dragon"),
    ("Side Story 100 - The Black Dragon", "Side Story 100: The Black Dragon"),
    ("Chapter 781  - Transportation", "Chapter 781: Transportation"),
    # --
    ("Chapter 100The Black Dragon", "Chapter 100: The Black Dragon"),
    ("Side Story 100The Black Dragon", "Side Story 100: The Black Dragon"),
    ("Chapter Side Story 100The Black Dragon", "Chapter Side Story 100: The Black Dragon"),
    # --
    ("Chapter 100 The Black Dragon", "Chapter 100: The Black Dragon"),
    ("Chapter 100.1 The Black Dragon", "Chapter 100.1: The Black Dragon"),
    ("Side Story 100 The Black Dragon", "Side Story 100: The Black Dragon"),
    ("Side Story 100.1 The Black Dragon", "Side Story 100.1: The Black Dragon"),
    ("Chapter Side Story 100 The Black Dragon", "Chapter Side Story 100: The Black Dragon"),
    ("Chapter Side Story 100.1 The Black Dragon", "Chapter Side Story 100.1: The Black Dragon"),
    # --
    ("Chapter 1321:  1321 Communication", "Chapter 1321: Communication"),
    ("Chapter 140:  Expansion? Full House!", "Chapter 140: Expansion? Full House!"),
    # --
    ("Chapter 620:  : Gone?!", "Chapter 620: Gone?!"),
    ("Chapter 100:   : The Black Dragon", "Chapter 100: The Black Dragon"),
    ("Chapter 100:   :   : The Black Dragon", "Chapter 100: The Black Dragon"),
    # --
    ("Book 1, 5", "Book 1: Chapter 5"),
    ("Book 1, 7A", "Book 1: Chapter 7A"),
    ("Book 1, 7B", "Book 1: Chapter 7B"),
    ("Book 1, 28B", "Book 1: Chapter 28B"),
    ("Book 1, 80 + AUDIO!", "Book 1: Chapter 80 + AUDIO!"),
    ("Book 6, 161 ", "Book 6: Chapter 161"),
    ("Book 6,161 ", "Book 6: Chapter 161"),
    ("Book 6,  161 ", "Book 6: Chapter 161"),
]


class CleanTitleTestCase(TestCase):
    def test_clean_title(self):
        for input_title, expected_output_title in TEST_CASES:
            with self.subTest(title_test=input_title):
                actual_output_title = data.Chapter.clean_title(input_title)
                self.assertEqual(actual_output_title, expected_output_title)
