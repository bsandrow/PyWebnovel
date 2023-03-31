"""A collection of utilities for XML-handling."""

from xml.dom.minidom import Document, Element


def set_element_attributes(element: Element, attributes: dict) -> None:
    """
    Take a dictionary and use the key-value pairs to set attribute values on an XML element.

    :param element: An XML element to set attributes on.
    :param attributes: A dictionary of to turn into attribute name-value pairs on the XML element.
    """
    for name, value in attributes.items():
        element.setAttribute(name, value)


def create_element(dom: Document, name: str, text: str = None, attributes: dict = None, parent: Element = None):
    """
    Create an XML element with a variety of options.

    :param dom: The Document to create the element in the context of.
    :param name: The name of the element tag. E.g. "str" would create element <str>.
    :param text: (optional) Set the text node of the element. E.g. <str>TEXT</str>
    :param attributes: (optional) A dictionary of attribute names/values to set on the element.
    :param parent: (optional) Set this new element as the child of this element.
    """
    element = dom.createElement(name)

    if text is not None:
        text_node = dom.createTextNode(text)
        element.appendChild(text_node)

    set_element_attributes(element, attributes or {})

    if parent is not None:
        parent.appendChild(element)

    return element
