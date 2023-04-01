import pkgutil
from unittest import TestCase, mock

from webnovel.epub import files2


class MetadataFileTestCase(TestCase):
    def test_generate(self):
        self.assertEqual(files2.MimetypeFile().generate(pkg=None), b"application/epub+zip")

    def test_from_dict(self):
        expected = files2.MimetypeFile()
        actual = files2.MimetypeFile.from_dict({"file_id": "mimetype", "filename": "mimetype"})
        self.assertEqual(actual, expected)


class ContainerXMLTestCase(TestCase):
    def test_generate(self):
        self.assertEqual(
            files2.ContainerXML().generate(pkg=None),
            (
                b'<?xml version="1.0" encoding="utf-8"?>'
                b'<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                b"<rootfiles>"
                b'<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
                b"</rootfiles>"
                b"</container>"
            ),
        )

    def test_from_dict(self):
        expected = files2.ContainerXML()
        actual = files2.ContainerXML.from_dict({"file_id": "container-xml", "filename": "META-INF/container.xml"})
        self.assertEqual(actual, expected)

    def test_to_dict(self):
        expected = {"file_id": "container-xml", "filename": "META-INF/container.xml", "mimetype": "", "title": None}
        actual = files2.ContainerXML().to_dict()
        self.assertEqual(actual, expected)


class StylesheetTestCase(TestCase):
    def test_generate(self):
        pkg = mock.Mock()
        pkg.extra_css = None
        actual = files2.Stylesheet().generate(pkg)
        expected = pkgutil.get_data("webnovel.epub", "content/stylesheet.css")
        self.assertEqual(actual, expected)

    def test_from_dict(self):
        expected = files2.Stylesheet()
        actual = files2.Stylesheet.from_dict({"file_id": "style", "filename": "OEBPS/stylesheet.css"})
        self.assertEqual(actual, expected)

    def test_to_dict(self):
        expected = {"file_id": "style", "filename": "OEBPS/stylesheet.css", "mimetype": "text/css", "title": None}
        actual = files2.Stylesheet().to_dict()
        self.assertEqual(actual, expected)
