from unittest import TestCase

from xml.dom.minidom import getDOMImplementation, Element

from webnovel.xml import create_element, set_element_attributes


class SetElementAttributesTestCase(TestCase):
    def test_handles_no_dict(self):
        element = Element("test")
        attrs = {}
        set_element_attributes(element, attrs)
        self.assertEqual(element.toxml(encoding="utf-8"), b"<test/>")

    def test_handles_dict(self):
        doc = getDOMImplementation().createDocument(None, "abc", None)
        element = doc.createElement("test")
        attrs = {"test1": "abc", "test2": "deF"}
        set_element_attributes(element, attrs)
        self.assertEqual(element.toxml(encoding="utf-8"), b"<test test1=\"abc\" test2=\"deF\"/>")


class CreateElementTestCase(TestCase):
    def test_handles_text(self):
        dom = getDOMImplementation().createDocument(None, "create-element", None)
        element = create_element(dom, name="sub-element", text="This is my text")
        self.assertEqual(
            element.toxml(encoding="utf-8"),
            b"<sub-element>This is my text</sub-element>"
        )

    def test_handles_attributes(self):
        dom = getDOMImplementation().createDocument(None, "create-element", None)
        attributes = {"colour": "red", "variety": "Red Delicious"}
        element = create_element(dom, name="apple", attributes=attributes)
        self.assertEqual(
            element.toxml(encoding="utf-8"),
            b"<apple colour=\"red\" variety=\"Red Delicious\"/>"
        )

    def test_handles_both(self):
        dom = getDOMImplementation().createDocument(None, "create-element", None)
        attributes = {"colour": "red", "variety": "Red Delicious"}
        text = "Created in 1872."
        element = create_element(dom, name="apple", attributes=attributes, text=text)
        self.assertEqual(
            element.toxml(encoding="utf-8"),
            b"<apple colour=\"red\" variety=\"Red Delicious\">Created in 1872.</apple>"
        )

    def test_handles_parent(self):
        dom = getDOMImplementation().createDocument(None, "create-element", None)
        element = create_element(dom, "apple", parent=dom.documentElement)
        self.assertEqual(element.parentNode, dom.documentElement)
        expected = (
            b"<?xml version=\"1.0\" encoding=\"utf-8\"?>"
            b"<create-element>"
            b"<apple/>"
            b"</create-element>"
        )
        self.assertEqual(dom.toxml(encoding="utf-8"), expected)
