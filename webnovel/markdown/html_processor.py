from dataclasses import dataclass
import itertools
from typing import Callable, List, Type, Union

from bs4.element import Tag

from .html import (
    AnchorElement,
    BoldElement,
    DivElement,
    HorizontalRuleElement,
    HtmlElementParser,
    ItalicElement,
    LineBreakElement,
    ParagraphElement,
)


@dataclass
class HtmlProcessorRule:
    element_class: Type[HtmlElementParser]
    rule: Union[str, Callable]

    def match(self, element: Tag) -> bool:
        if isinstance(self.rule, str):
            return element.tag.lower() == self.rule.lower()

        if callable(self.rule):
            return self.rule(element)

        raise ValueError(f"Bad Rule: {self.rule}")


class HtmlProcessor:
    rules: List[HtmlProcessorRule] = None
    default_rules: List[HtmlProcessorRule] = [
        HtmlProcessorRule(DivElement, "div"),
        HtmlProcessorRule(BoldElement, "b"),
        HtmlProcessorRule(BoldElement, "strong"),
        HtmlProcessorRule(ItalicElement, "i"),
        HtmlProcessorRule(ItalicElement, "em"),
        HtmlProcessorRule(AnchorElement, "a"),
        HtmlProcessorRule(LineBreakElement, "br"),
        HtmlProcessorRule(HorizontalRuleElement, "hr"),
        HtmlProcessorRule(ParagraphElement, "p"),
        HtmlProcessorRule(HtmlElementParser, lambda element: True),
    ]

    def __init__(self, rules: List[HtmlProcessorRule] = None):
        self.rules = rules or []

    def get_element_parser(self, element: Tag) -> HtmlElementParser:
        return self.get_class(element)(processor=self, element=element)

    def get_class(self, element: Tag) -> Type[HtmlElementParser]:
        for rule in itertools.chain(self.rules, self.default_rules):
            if rule.match(element):
                return rule.element_class
        return HtmlElementParser

    def coerce_to_markdown(self, item: Union[str, Tag]) -> str:
        return self.get_element_parser(item).to_markdown() if isinstance(item, Tag) else item
