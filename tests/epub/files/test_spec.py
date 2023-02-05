from unittest import TestCase

from webnovel.epub.data import EpubNovel
from webnovel.epub.pkg import EpubPackage
from webnovel.epub.files import MimetypeFile, ContainerXML


class MimetypeFileTestCase(TestCase):
    def setUp(self):
        self.pkg_file = EpubPackage(
            filename="test.epub",
            novel=EpubNovel(url="URL", title="TITLE"),
        )
        self.mimetype_file = MimetypeFile(pkg=self.pkg_file)

    def test_filename(self):
        self.assertEqual(self.mimetype_file.filename, "mimetype")

    def test_data(self):
        self.assertEqual(self.mimetype_file.data, b"application/epub+zip")


class ContainerXMLTestCase(TestCase):
    def test_filename(self):
        self.assertEqual(ContainerXML.filename, "META-INF/container.xml")

    def test_generate(self):
        pkg = EpubPackage(
            filename="test.epub",
            novel=EpubNovel(url="URL", title="TITLE"),
        )
        container_xml = ContainerXML(pkg)

        self.assertIsNone(container_xml.data)
        container_xml.generate()
        print(container_xml.data)
        self.assertEqual(
            container_xml.data,
            (
                b'<?xml version="1.0" encoding="utf-8"?>'
                b'<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                b'<rootfiles>'
                b'<rootfile full-path="package.opf" media-type="application/oebps-package+xml"/>'
                b'</rootfiles>'
                b'</container>'
            )
        )