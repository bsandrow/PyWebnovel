from xml.dom.minidom import Element, Document


def set_element_attributes(element: Element, attributes: dict) -> None:
    for name, value in attributes.items():
        element.setAttribute(name, value)


def create_element(dom: Document, name: str, text: str = None, attributes: dict = None, parent: Element = None):
    element = dom.createElement(name)

    if text is not None:
        text_node = dom.createTextNode(text)
        element.appendChild(text_node)

    set_element_attributes(element, attributes or {})

    if parent is not None:
        parent.appendChild(element)

    return element


