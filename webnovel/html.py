"""HTML-Processing Tools."""

from abc import ABCMeta, abstractmethod
import functools
import hashlib
import re
from typing import Union

from bs4 import Comment, NavigableString, Tag
import imgkit

#
# Default list of attributes to keep for all elements.
#
DEFAULT_WHITELIST = ["style", "id", "title", "dir", "lang", "translate"]

#
# Whitelist of attribute names that are specific to certain HTML tags.
#
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

#
# List of HTML tags to check for empty content. Elements with no content under
# them will be filtered out. Used by the "remove_blank_elements" filter.
#
EMPTY_CONTENT_ELEMENTS = ["div", "h1", "h2", "h3", "h4", "h5", "h6", "p"]

#
# List of HTML tags that should just be blanket removed from content.
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
# Regex patterns for for removing sections of chapter content.
#
CONTENT_WARNING_PATTERNS = [
    # re.compile(
    #     r"^\s*The source of this content is " + r".{0,4}".join(build_replacements("novelbin.net")), re.IGNORECASE
    # ),
    re.compile(r"^\s*Read\s*the\s*webtoon\s*on\s*http", re.IGNORECASE),
    re.compile(r"^\s*Join\s*our\s*discord", re.IGNORECASE),
]

FILTERS = {}
DEFAULT_FILTERS = []


def register_html_filter(name: str = None, is_default: bool = False):
    """
    Register a function as an HTML filter with a name used to reference it.

    :param name: (optional) The name of the filter. This will be used to
        reference the filter. The default is to pull the name from the function.
    :param is_default: (optional) If true, then the filter's name will be added
        to the list of default filters.
    """

    def _register_html_filter(f):
        _name = name or f.__name__
        FILTERS[_name] = f
        if is_default:
            DEFAULT_FILTERS.append(_name)
        return f

    return _register_html_filter


@register_html_filter(name="remove_blacklisted_elements", is_default=True)
def element_blacklist_filter(html: Tag) -> None:
    """
    Remove matching elements (and their subtrees) from the provided HTML tree.

    :param html: The HTML element / tree to filter.
    """
    for element in html(ELEMENT_BLACKLIST):
        element.decompose()


@register_html_filter(name="remove_blank_elements", is_default=True)
def empty_content_filter(html: Tag) -> None:
    """
    Filter matching elements from the HTML tree if they have no content / child elements.

    :param html: A BeautifulSoup Tag instance.
    """
    for element in html(EMPTY_CONTENT_ELEMENTS):
        # If contents are just a string of whitespace then you'll end up with something like: [' ']
        # need to filter this down to [] so it hits the if-statment.
        contents = [item for item in element.contents if not isinstance(item, str) or item.strip()]
        if not contents:
            element.decompose()


@register_html_filter(name="remove_hidden_elements", is_default=True)
def hidden_elements_filter(html: Tag) -> None:
    """
    Remove hidden elements from the HTML.

    At the current time, this is just removing any elements that have "display:
    none" directly set on the style of the element.
    """
    for tag in html.find_all(style=True):
        style = parse_style(tag["style"])
        if style.get("display") == "none":
            tag.decompose()


@register_html_filter(name="remove_comments", is_default=True)
def remove_comments_filter(html: Tag) -> None:
    """Remove all HTML comments from the tree."""
    for tag in html.find_all(string=lambda text: isinstance(text, Comment)):
        remove_element(tag)


@register_html_filter(name="remove_useless_attrs", is_default=False)
def useless_attributes_filter(html: Tag) -> None:
    """
    Filter out all attributes except the ones in the whitelist for that particular tag.

    Some tags have specific attributes that they need, so some have expanded whitelists as compared to the default
    whitelist for most of the elements.
    """
    for tag in html.find_all():
        tag_name = tag.name.lower()
        whitelist = TAG_SPECIFIC_WHITELIST.get(tag_name, DEFAULT_WHITELIST)
        for attr_name in tuple(tag.attrs):
            if attr_name.lower() not in whitelist:
                del tag[attr_name]


@register_html_filter(name="remove_content_warnings", is_default=True)
def content_warnings_filter(html: Tag) -> None:
    """
    Remove Content Warnings from the tree.

    The list of patterns is passed in manually since many sites will have specific patterns for them.
    """
    """Filter all <p> tags that have text that matches the pattern."""
    for tag in html(["p"]):
        for pattern in CONTENT_WARNING_PATTERNS:
            if pattern.match(tag.text) is not None:
                tag.decompose()


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


def parse_style(style_value: str) -> dict:
    """Parse the value of a style= HTML attribute into a dictionary of values."""
    style_attrs = {}
    for item in re.split(r"\s*;\s*", style_value):
        if ":" in item:
            name, _, value = item.partition(":")
            style_attrs[name.strip()] = value.strip()
    return style_attrs


def calculate_table_size(table: Tag) -> int:
    """
    Return the total number of columns in an HTML <table> element.

    :params table: A Tag instance for a <table>. Assumed to have <tr> and <td>
        elements.
    """
    assert table.name == "table", "Cannot calculate the size of a non-<table> element."
    table_size = 0
    for row in table.find_all("tr"):
        row_size = 0
        for cell in row.find_all("td"):
            row_size += int(cell.get("colspan", "1"))
        table_size = max((table_size, row_size))
    return table_size


def convert_table_to_image(table: Tag, imgkit_options: dict = None) -> tuple[bytes, str, str]:
    """
    Generate an image of a <table> element.

    Returns a tuple of (IMAGE_DATA, IMAGE_MIMETYPE, IMAGE_DATA_HASH)

    :param table: a <table> element.
    :param imgkit_options: A dict of options to pass to imgkit. If not passed,
        then format defaults to png and width to 600.
    """
    assert table.name == "table", "Cannot calculate the size of a non-<table> element."
    imgkit_options = imgkit_options or {}
    imgkit_options.setdefault("format", "png")
    imgkit_options.setdefault("width", "600")
    mimetype = "image/" + imgkit_options["format"]
    image_data = imgkit.from_string(str(table), False, imgkit_options)
    image_hash = hashlib.sha256(image_data).hexdigest()
    return (image_data, mimetype, image_hash)


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


def run_filters(html: Tag, filters: list[str] = None) -> None:
    """
    Run a list of filters against the provided HTML tree.

    :param html: The Tag to filter content from.
    :param filters: (optional) The list of filters to apply. Defaults to DEFAULT_FILTERS list.
    """
    if filters is None:
        filters = tuple(DEFAULT_FILTERS)

    for filter_name in filters:
        _filter = FILTERS.get(filter_name)
        if not _filter:
            raise ValueError(f"No such filter: {filter_name}")
        _filter(html)
