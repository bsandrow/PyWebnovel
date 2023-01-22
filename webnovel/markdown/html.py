from contextlib import contextmanager
import logging
import re
from typing import Type

from bs4.element import Tag

# from wns.config import get_boolean_env_var

# DEBUG_HTML = get_boolean_env_var("DEBUG_HTML")
logging.basicConfig()
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG if DEBUG_HTML else logging.INFO)


# def debug_result(func):
#     def wrapper(*args, **kwargs):
#         result = func(*args, **kwargs)
#         self = args[0]
#         logger.debug("%s.%s: %r", self.__class__.__name__, func.__name__, result)
#         return result
#     return wrapper


class HtmlElementParser:
    STRIP_WHITESPACE: bool = False

    processor = None

    def __init__(self, processor, element: Tag) -> None:
        from .html_processor import HtmlProcessor
        self.element = element
        self.processor: HtmlProcessor = processor

    def debug(self, func, message, *args, **kwargs):
        logger.debug("%s.%s: " + message, self.__class__.__name__, func, *args, **kwargs)

    # @debug_result
    def convert_text(self) -> str:
        result = self.element.text or ""
        # self.debug("convert_text", repr(result))
        return result

    def convert_tail(self) -> str:
        return self.element.tail or ""

    def convert_children(self) -> str:
        return "".join(
            self.processor.get_element_parser(child).to_markdown()
            for child in self.element.children
        )

    def convert_body(self) -> str:
        text = self.convert_text()
        if self.STRIP_WHITESPACE:
            text = text.strip()
        children_text = self.convert_children()
        return text + children_text

    def to_markdown(self):
        result = self.convert_body() + self.convert_tail()
        return result


class BoldElement(HtmlElementParser):
    def convert_body(self) -> str:
        body_orig = super().convert_body()
        match = re.match(r"^(\W*)(.*?)(\W*)$", body_orig)
        pre_whitespace = match.group(1)
        body = match.group(2)
        post_whitespace = match.group(3)
        if not body:
            return body_orig
        return f"{pre_whitespace}**{body}**{post_whitespace}"


class ItalicElement(HtmlElementParser):
    def convert_body(self) -> str:
        body_orig = super().convert_body()
        match = re.match(r"^(\W*)(.*?)(\W*)$", body_orig)
        pre_whitespace = match.group(1)
        body = match.group(2)
        post_whitespace = match.group(3)
        if not body:
            return body_orig
        return f"{pre_whitespace}_{body}_{post_whitespace}"


# TODO keep_links functionality
class AnchorElement(HtmlElementParser):
    @debug_result
    def to_markdown(self) -> str:
        body = self.convert_body()
        if body.strip():
            return f"[{body}]({self.element.attrib.get('href')})" + self.convert_tail()
        return self.convert_tail()


class LineBreakElement(HtmlElementParser):
    @debug_result
    def to_markdown(self) -> str:
        return f"\n{self.convert_tail()}"


class ParagraphElement(HtmlElementParser):
    @debug_result
    def to_markdown(self) -> str:
        body = self.convert_body()
        body = re.sub(r"\n+$", "", body)  # remove trailing newlines
        tail = re.sub(r"^\n+", "", self.convert_tail())
        return f"{body}\n\n{tail}"


class HorizontalRuleElement(HtmlElementParser):
    @debug_result
    def to_markdown(self) -> str:
        return "<div style=\"font-weight: bold; text-align: center; font-size: 120%\"> *** </div>" + self.convert_tail()


class DivElement(HtmlElementParser):
    def convert_body(self):
        return re.sub(r"\n+$", "", super().convert_body()) + "\n\n"


DEFAULT_HANDLER_MAP = {}


def default_handler(handler: Type["TagHandler"]) -> None:
    if not issubclass(handler, TagHandler):
        raise ValueError(f"Only TagHandler subclasses can be default handlers.")
    DEFAULT_HANDLER_MAP[handler.tag_name] = handler


class Processor:
    HANDLERS: list[Type["HtmlHandler"]] = None

    def get_default_handler(self, node: Tag) -> Type["HtmlHandler"]:
        """Return the default TagHandler class for this node's tag."""
        return DEFAULT_HANDLER_MAP[node.name]

    def get_handler(self, node: Tag):
        for handler in self.HANDLERS or []:
            if handler.handles(node):
                return handler

        return self.get_default_handler(node)

    def parse(self, tag: Tag):
        pass


class HtmlHandler:
    @classmethod
    def handles(cls, node: Tag) -> bool:
        raise NotImplementedError


class TagHandler(HtmlHandler):
    tag_name: str

    @classmethod
    def handles(cls, node: Tag) -> bool:
        return node.name.lower() == cls.tag_name.lower()


@default_handler
class LineBreakHandler(TagHandler):
    tag_name = "br"


@default_handler
class DivHandler(TagHandler):
    tag_name = "div"
