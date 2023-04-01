import re
from unittest import TestCase

from bs4 import BeautifulSoup

from webnovel import html


class ParseStyleTestCase(TestCase):
    def test_parse_single_item_with_no_semicolon(self):
        actual = html.parse_style("display: none")
        expected = {"display": "none"}
        self.assertEqual(actual, expected)

    def test_parse_single_item_with_trailing_semicolon(self):
        actual = html.parse_style("display: none;")
        expected = {"display": "none"}
        self.assertEqual(actual, expected)

    def test_parse_multiple_items(self):
        actual = html.parse_style("display: none; flex: none; width: 40%;")
        expected = {"display": "none", "flex": "none", "width": "40%"}
        self.assertEqual(actual, expected)

    def test_handles_extra_whitespace(self):
        actual = html.parse_style("display : none; flex :none; width: 40%;")
        expected = {"display": "none", "flex": "none", "width": "40%"}
        self.assertEqual(actual, expected)


class ElementBlacklistFilterTestCase(TestCase):
    def test_removes_specified_elements(self):
        soup = BeautifulSoup(("<div>" "<style></style>" "<p>EXAMPLE</p>" "</div>"), "html.parser")
        html.ElementBlacklistFilter(tag_name_blacklist=["style"]).filter(soup)
        self.assertEqual(str(soup), "<div><p>EXAMPLE</p></div>")


class EmptyContentFilterTestCase(TestCase):
    def test_remove_tags_with_empty_content(self):
        soup = BeautifulSoup(
            ("<div>" "<style></style>" "<p></p>" "<p>EXAMPLE<p> </p></p>" "<p></p>" "<div></div>" "</div>"),
            "html.parser",
        )
        html.EmptyContentFilter(tag_names=["p"]).filter(soup)
        self.assertEqual(str(soup), "<div><style></style><p>EXAMPLE</p><div></div></div>")


class DisplayNoneFilterTestCase(TestCase):
    def test_removes_tags_with_display_none(self):
        soup = BeautifulSoup(
            (
                "<div>"
                "<style></style>"
                '<p style="display: none;"></p>'
                "<p>EXAMPLE<p> </p></p>"
                '<p style="display: inline-block;"></p>'
                "<p></p>"
                "<div></div>"
                "</div>"
            ),
            "html.parser",
        )
        html.DisplayNoneFilter().filter(soup)
        self.assertEqual(
            str(soup),
            (
                "<div>"
                "<style></style>"
                "<p>EXAMPLE<p> </p></p>"
                '<p style="display: inline-block;"></p>'
                "<p></p>"
                "<div></div>"
                "</div>"
            ),
        )


class StripeUselessAttributesTestCase(TestCase):
    def test_strips_anchor_attributes_correctly(self):
        tag_names = tuple(html.StripUselessAttributes.TAG_SPECIFIC_WHITELIST.keys())
        single_element_tags = ["img"]

        for tag_name in tag_names:
            for attr in html.StripUselessAttributes.TAG_SPECIFIC_WHITELIST[tag_name]:
                with self.subTest(tag_name=tag_name, attr=attr):
                    if tag_name in single_element_tags:
                        soup = BeautifulSoup(f'<div><{tag_name} {attr}="a" test="a" data="a"/></div>', "html.parser")
                        html.StripUselessAttributes().filter(soup)
                        self.assertEqual(str(soup), f'<div><{tag_name} {attr}="a"/></div>')

                    else:
                        soup = BeautifulSoup(
                            f'<div><{tag_name} {attr}="a" test="a" wire:id="45" data="a"></{tag_name}></div>',
                            "html.parser",
                        )
                        html.StripUselessAttributes().filter(soup)
                        self.assertEqual(str(soup), f'<div><{tag_name} {attr}="a"></{tag_name}></div>')


class StripCommentsTestCase(TestCase):
    def test_removes_comments(self):
        soup = BeautifulSoup(
            (
                "<div>"
                "<!-- <style></style> -->"
                '<p style="display: none;"></p>'
                "<!-- <!-- <p>EXAMPLE<p> </p></p> -->"
                "<p></p>"
                "<!-- Comment -->"
                "<div></div>"
                "</div>"
            ),
            "html.parser",
        )
        html.StripComments().filter(soup)
        self.assertEqual(str(soup), ("<div>" '<p style="display: none;"></p>' "<p></p>" "<div></div>" "</div>"))


class RunFiltersTestCase(TestCase):
    def test_run_filters(self):
        filters = [
            html.DisplayNoneFilter(),
            html.StripComments(),
        ]
        soup = BeautifulSoup(
            (
                "<div>"
                "<!-- <style></style> -->"
                '<p style="display: none;"></p>'
                "<!-- <!-- <p>EXAMPLE<p> </p></p> -->"
                "<p></p>"
                "<!-- Comment -->"
                "<div></div>"
                "</div>"
            ),
            "html.parser",
        )
        html.run_filters(soup, filters=filters)
        self.assertEqual(str(soup), ("<div>" "<p></p>" "<div></div>" "</div>"))

    def test_run_default_filters(self):
        soup = BeautifulSoup(
            (
                "<div>"
                "<!-- <style></style> -->"
                '<p style="line-height: 2;">Join our discord for updates on releases! <a href="https://dsc.gg/reapercomics">https://dsc.gg/reapercomics</a></p>'
                "<p>This is content.</p>"
                '<p style="line-height: 2;">Read the webtoon on <a href="https://example.com" aria-invalid="true">https://example.com/webtoon/</a></p>'
                '<p style="display: none;"></p>'
                "<!-- <!-- <p>EXAMPLE<p> </p></p> -->"
                "<p></p>"
                "<!-- Comment -->"
                "<div></div>"
                "</div>"
            ),
            "html.parser",
        )
        html.run_filters(soup)
        self.assertEqual(str(soup), ("<div>" "<p>This is content.</p>" "</div>"))


class ContentWarningFilterTestCase(TestCase):
    def test_content_warning(self):
        soup = BeautifulSoup(
            (
                "<div>"
                '<p style="line-height: 2;">Join our discord for updates on releases! <a href="https://dsc.gg/reapercomics">https://dsc.gg/reapercomics</a></p>'
                "<p>This is content.</p>"
                '<p style="line-height: 2;">Read the webtoon on <a href="https://example.com" aria-invalid="true">https://example.com/webtoon/</a></p>'
                "</div>"
            ),
            "html.parser",
        )
        html.ContentWarningFilter(html.CONTENT_WARNING_PATTERNS).filter(soup)
        self.assertEqual(str(soup), ("<div>" "<p>This is content.</p>" "</div>"))
