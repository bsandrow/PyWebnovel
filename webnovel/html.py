"""HTML-Processing Tools."""

from abc import ABCMeta, abstractmethod
import re
from typing import Union

from bs4 import Comment, NavigableString, Tag

#
# These are elements that we absolutely want to strip out of the story content.
#
ELEMENT_BLACKLIST = [
    "noscript",
    "form",
    "fieldset",
    "video",
    "script",
    "head",
    "meta",
    "select",
    "textarea",
    "audio",
    "canvas",
]

#
# Elements to treat as a block when converting to Markdown.
#
BLOCK_ELEMENTS = [
    "address",
    "article",
    "aside",
    "canvas",
    "div",
    "figcaption",
    "footer",
    "header",
    "main",
    "nav",
    "section",
]


#
# Content Warning Patterns
#
def build_replacements(string_value: str):
    """
    Return string as a list of characters with some replaced with patterns.

    Some characters have look-alike characters in unicode. This will replace those characters with a [] pattern
    containing the character itself in addition to some of its "substitutes."
    """
    return [
        {
            "o": "[o0∅]",
            "u": "[u∪⋃]",
            "n": "[n⋂∩]",
            "v": "[v⋁√]",
            "a": "[a⋀∆∀]",
            "c": "[c∁]",
            "e": "[e∃∊⋿]",
            "s": "[∫s]",
        }.get(char.lower(), char)
        for char in string_value
    ]


CONTENT_WARNING_PATTERNS = [
    re.compile(
        r"^\s*The source of this content is " + r".{0,4}".join(build_replacements("novelbin.net")), re.IGNORECASE
    ),
    re.compile(r"^\s*Read\s*the\s*webtoon\s*on\s*http", re.IGNORECASE),
    re.compile(r"^\s*Join\s*our\s*discord", re.IGNORECASE),
]


def parse_style(style_value: str) -> dict:
    """Parse the value of a style= HTML attribute into a dictionary of values."""
    style_attrs = {}
    for item in re.split(r"\s*;\s*", style_value):
        if ":" in item:
            name, _, value = item.partition(":")
            style_attrs[name.strip()] = value.strip()
    return style_attrs


# <blockquote>
# "dd",
# "dl",
# <dt>
# <figure>
# <h1>-<h6>
# <hr>
# <li>
# "ol",
# <p>
# <pre>
# <table>
# <tfoot>
# <ul>


def remove_element(element: Union[Tag, NavigableString]) -> None:
    """
    Remove element from the tree.

    Only Tag instances have decompose() which not only removes the item from the tree, but also immediately destroys the
    instance itself.  Both Tag and NavigableString have extract() which only removes them from the tree. This uses
    decompose() if it exists, otherwise extract(). This allows for memory to be freed up sooner in places where the
    instance is no longer needed after being removed from the tree.
    """
    if hasattr(element, "decompose"):
        element.decompose()
    else:
        element.extract()


class HtmlFilter(metaclass=ABCMeta):
    """Base class for filtering content from an HTML tree starting with an Element/Tag."""

    # noinspection PyMethodMayBeStatic
    @abstractmethod
    def filter(self, html_tree: Tag) -> None:
        """Transform (aka "filter") the content."""


class ElementBlacklistFilter(HtmlFilter):
    """Filter to remove all blacklisted elements from the tree."""

    def __init__(self, tag_name_blacklist: list[str]) -> None:
        self.blacklist = tag_name_blacklist

    def filter(self, html_tree: Tag) -> None:
        """
        Remove matching elements (and their subtrees) from the provided HTML tree.

        :param html_tree: The HTML element / tree to filter.
        """
        for element in html_tree(self.blacklist):
            element.decompose()


class EmptyContentFilter(HtmlFilter):
    """Filter out elements that are useless."""

    tag_names: list

    def __init__(self, tag_names: list[str]) -> None:
        self.tag_names = tag_names

    def filter(self, html_tree: Tag) -> None:
        """Filter matching elements from the HTML tree if they have no content / child elements."""
        for element in html_tree(self.tag_names):
            # If contents are just a string of whitespace then you'll end up with something like: [' ']
            # need to filter this down to [] so it hits the if-statment.
            contents = [item for item in element.contents if not isinstance(item, str) or item.strip()]
            if not contents:
                element.decompose()


class ContentWarningFilter(HtmlFilter):
    """
    Remove Content Warnings from the tree.

    The list of patterns is passed in manually since many sites will have specific patterns for them.
    """

    def __init__(self, content_warning_patterns: list[re.Pattern]) -> None:
        self.content_warning_patterns = content_warning_patterns

    def filter(self, html_tree: Tag) -> None:
        """Filter all <p> tags that have text that matches the pattern."""
        for tag in html_tree(["p"]):
            for pattern in self.content_warning_patterns:
                if pattern.match(tag.text) is not None:
                    tag.decompose()


class DisplayNoneFilter(HtmlFilter):
    """Filter For 'display: none;' Elements."""

    def filter(self, html_tree: Tag) -> None:
        """Filter out all elements have have 'display: none;' in the style attribute."""
        for tag in html_tree.find_all(style=True):
            style = parse_style(tag["style"])
            if style.get("display") == "none":
                tag.decompose()


class StripUselessAttributes(HtmlFilter):
    """Filter that removes all HTML attributes that are useless for the purposes of an ebook."""

    DEFAULT_WHITELIST = ["style", "id", "title", "dir", "lang", "translate"]
    TAG_SPECIFIC_WHITELIST = {
        "img": ["src", "srcset", "alt", "width", "height"] + DEFAULT_WHITELIST,
        "a": ["href", "hreflang", "rel", "target", "type", "media"] + DEFAULT_WHITELIST,
        "th": ["colspan", "headers", "rowspan", "scope", "abbr"] + DEFAULT_WHITELIST,
        "td": ["colspan", "headers", "rowspan", "scope", "abbr"] + DEFAULT_WHITELIST,
        "colgroup": ["span"] + DEFAULT_WHITELIST,
        "var": ["code", "samp", "kbd", "pre"] + DEFAULT_WHITELIST,
        "time": ["datetime"] + DEFAULT_WHITELIST,
        # "source": ["src", "type"] + DEFAULT_WHITELIST,
    }

    def filter(self, html_tree: Tag) -> None:
        """
        Filter out all attributes except the ones in the whitelist for that particular tag.

        Some tags have specific attributes that they need, so some have expanded whitelists as compared to the default
        whitelist for most of the elements.
        """
        for tag in html_tree.find_all():
            tag_name = tag.name.lower()
            whitelist = self.TAG_SPECIFIC_WHITELIST.get(tag_name, self.DEFAULT_WHITELIST)
            for attr_name in tuple(tag.attrs):
                if attr_name.lower() not in whitelist:
                    del tag[attr_name]


class StripComments(HtmlFilter):
    """Strip all HTML comments from the tree."""

    def filter(self, html_tree: Tag) -> None:
        """Walk the tree removing Comment instances."""
        for tag in html_tree.find_all(string=lambda text: isinstance(text, Comment)):
            remove_element(tag)


#
# The default list of filters. Most uses of filters will probably just add filters to this default list rather than
# completely replace it.
#
DEFAULT_FILTERS: tuple[HtmlFilter] = (
    ElementBlacklistFilter(ELEMENT_BLACKLIST),
    EmptyContentFilter(["div", "h1", "h2", "h3", "h4", "h5", "h6", "p"]),
    ContentWarningFilter(CONTENT_WARNING_PATTERNS),
    DisplayNoneFilter(),
    StripComments(),
)


def run_filters(html_tree: Tag, filters: list[HtmlFilter] = None):
    """
    Run a list of filters against the provided HTML tree.

    :param html_tree: The Tag to filter content from.
    :param filters: (optional) The list of filters to apply. Defaults to DEFAULT_FILTERS list.
    """
    if filters is None:
        filters = tuple(DEFAULT_FILTERS)

    for html_filter in filters:
        html_filter.filter(html_tree)
