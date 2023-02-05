# import io
# from unittest import TestCase, mock
# from zipfile import ZipFile
#
# from xml.dom.minidom import getDOMImplementation, Element
#
# from webnovel.data import Image, Novel, Person
# from webnovel.epub.data import EpubNovel
# from webnovel.epub.pkg import (
#     Epub3Refs,
#     EpubPackage,
#     EpubImages,
#     EpubImage,
#     CoverPage,
#     TitlePage,
# )
#
# from ..helpers import get_test_data
#
#
# class Epub3RefsTestCase(TestCase):
#     def test_get_tag_id(self):
#         dom = getDOMImplementation().createDocument(None, "refs-test", None)
#         epub3_refs = Epub3Refs(dom)
#         self.assertEqual(epub3_refs.get_tag_id(), "id-000")
#         self.assertEqual(epub3_refs.get_tag_id(), "id-001")
#
#     def test_get_tag_id_handles_different_format(self):
#         dom = getDOMImplementation().createDocument(None, "refs-test", None)
#         epub3_refs = Epub3Refs(dom)
#         with mock.patch.object(epub3_refs, "tag_id_fmt", "my-id-{counter}"):
#             self.assertEqual(epub3_refs.get_tag_id(), "my-id-0")
#             self.assertEqual(epub3_refs.get_tag_id(), "my-id-1")
#
#     def test_add_ref_handles_bkp_reftype(self):
#         dom = getDOMImplementation().createDocument(None, "refs-test", None)
#         epub3_refs = Epub3Refs(dom)
#         epub3_refs.add_ref(ref_type="aut", ref_property="prop1", tag_id="id-001")
#         epub3_refs.add_ref(ref_type="bkp", ref_property="prop1", tag_id="id-001")
#         epub3_refs.add_ref(ref_type="main", ref_property="prop1", tag_id="id-001")
#         actual = [ref.toxml(encoding="utf-8") for ref in epub3_refs.refs]
#         expected = [
#             b"<meta property=\"prop1\" refines=\"#id-001\" scheme=\"marc:relators\">aut</meta>",
#             b"<meta property=\"prop1\" refines=\"#id-001\" scheme=\"marc:relators\">bkp</meta>",
#             b"<meta property=\"prop1\" refines=\"#id-001\">main</meta>",
#         ]
#         self.assertEqual(actual, expected)
#
#
# class EpubPackageTestCase(TestCase):
#     maxDiff = None
#
#     @classmethod
#     def setUpClass(cls) -> None:
#         cls.test_png = Image(
#             url="file:///test-image.png",
#             data=get_test_data("test-image.png", use_bytes=True),
#             mimetype="image/png",
#             did_load=True,
#         )
#         cls.test_jpg = Image(
#             url="file:///test-image.jpg",
#             data=get_test_data("test-image.jpg", use_bytes=True),
#             mimetype="image/jpg",
#             did_load=True,
#         )
#
#     def test_is_epub3_property(self):
#         novel = EpubNovel(url="https://example.com/novel-name", title="Novel Name")
#         self.assertTrue(EpubPackage(filename="test.epub", novel=novel).is_epub3)
#         self.assertTrue(EpubPackage(filename="test.epub", novel=novel, version="3.0").is_epub3)
#         self.assertTrue(EpubPackage(filename="test.epub", novel=novel, version="3").is_epub3)
#         self.assertTrue(EpubPackage(filename="test.epub", novel=novel, version="3.1").is_epub3)
#         self.assertFalse(EpubPackage(filename="test.epub", novel=novel, version="4.0").is_epub3)
#         self.assertFalse(EpubPackage(filename="test.epub", novel=novel, version="2.0").is_epub3)
#
#     def test_get_container_xml(self):
#         novel = EpubNovel(url="https://example.com/novel-name", title="Novel Name")
#         epub = EpubPackage(filename="test.epub", novel=novel)
#
#         self.assertEqual(
#             epub.get_container_xml(),
#             (
#                 "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
#                 "<container version=\"1.0\" xmlns=\"urn:oasis:names:tc:opendocument:xmlns:container\">"
#                 "<rootfiles>"
#                 f"<rootfile full-path=\"{epub.pkg_opf_path}\" media-type=\"application/oebps-package+xml\"/>"
#                 "</rootfiles>"
#                 "</container>"
#             ).encode("utf-8")
#         )
#
#     def test_get_package_opf(self):
#         novel = EpubNovel(url="https://example.com/novel-name", title="Novel Name")
#         epub = EpubPackage(filename="test.epub", novel=novel)
#         self.assertEqual(
#             epub.get_package_opf(),
#             (
#                 f"<?xml version=\"1.0\" encoding=\"utf-8\"?>"
#                 f"<package version=\"3.0\" xmlns=\"http://www.idpf.org/2007/opf\" unique-identifier=\"pywebnovel-uid\">"
#                 f"<metadata xmlns:dc=\"http://purl.org/dc/elements/1.1/\" xmlns:opf=\"http://www.idpf.org/2007/opf\">"
#                 f"<dc:title id=\"id-000\">{novel.title}</dc:title>"
#                 f"<dc:contributor id=\"id-001\">PyWebnovel [https://github.com/bsandrow/PyWebnovel]</dc:contributor>"
#                 f"<dc:language>en</dc:language>"
#                 f"<dc:identifier>URL:https://example.com/novel-name</dc:identifier>"
#                 f"<dc:source>https://example.com/novel-name</dc:source>"
#                 f"<meta property=\"title-type\" refines=\"#id-000\">main</meta>"
#                 f"<meta property=\"role\" refines=\"#id-001\" scheme=\"marc:relators\">bkp</meta>"
#                 f"</metadata>"
#                 f"<manifest>"
#                 f"<item id=\"ncx\" href=\"toc.ncx\" media-type=\"application/x-dtbncx+xml\"/>"
#                 f"<item id=\"style\" href=\"OEBPS/stylesheet.css\" media-type=\"text/css\"/>"
#                 f"<item id=\"pywebnovel-meta\" href=\"pywebnovel.json\" media-type=\"application/json\"/>"
#                 f"<item id=\"title_page\" href=\"OEBPS/title_page.xhtml\" media-type=\"application/xhtml+xml\"/>"
#                 f"<item href=\"nav.xhtml\" id=\"nav\" media-type=\"application/xhtml+xml\" properties=\"nav\"/>"
#                 f"</manifest>"
#                 f"<spine toc=\"ncx\"><itemref idref=\"title_page\" linear=\"yes\"/></spine>"
#                 f"</package>"
#             ).encode("utf-8")
#         )
#
#     def test_metadata_includes_cover_image(self):
#         novel = EpubNovel(url="https://example.com/novel-name", title="Novel Name")
#         epub = EpubPackage(filename="test.epub", novel=novel)
#         epub.images.add(self.test_png, is_cover_image=True)
#         self.assertIn(b"<meta name=\"cover\" content=\"image000\"/>", epub.get_package_opf())
#
#     def test_save_adds_mimetype_file(self):
#         novel = EpubNovel(url="https://example.com/novel-name", title="Novel Name")
#         epub = EpubPackage(filename="test.epub", novel=novel)
#         fh = io.BytesIO()
#         epub.save(file_or_io=fh)
#         zipfile = ZipFile(fh, "r")
#         file_contents = zipfile.read("mimetype")
#         self.assertEqual(file_contents, b"application/epub+zip")
#
#     def test_save_adds_container_xml(self):
#         novel = EpubNovel(url="https://example.com/novel-name", title="Novel Name")
#         epub = EpubPackage(filename="test.epub", novel=novel)
#         fh = io.BytesIO()
#         epub.save(file_or_io=fh)
#         zipfile = ZipFile(fh, "r")
#         file_contents = zipfile.read("META-INF/container.xml")
#         self.assertEqual(file_contents, epub.get_container_xml())
#
#     def test_save_adds_package_opf(self):
#         novel = EpubNovel(url="https://example.com/novel-name", title="Novel Name")
#         epub = EpubPackage(filename="test.epub", novel=novel)
#         fh = io.BytesIO()
#         epub.save(file_or_io=fh)
#         zipfile = ZipFile(fh, "r")
#         file_contents = zipfile.read(epub.pkg_opf_path)
#         self.assertIsNotNone(file_contents)
#         self.assertEqual(file_contents, epub.get_package_opf())
#
#     def test_handles_non_cover_images(self):
#         novel = EpubNovel(url="https://example.com/novel-name", title="Novel Name")
#         epub = EpubPackage(filename="test.epub", novel=novel)
#         epub.images.add(self.test_png)
#         epub.images.add(self.test_jpg)
#         fh = io.BytesIO()
#         epub.save(file_or_io=fh)
#
#         zipfile = ZipFile(fh, "r")
#         png_contents = zipfile.read("OEBPS/image000.png")
#         jpg_contents = zipfile.read("OEBPS/image001.jpg")
#
#         self.assertIsNotNone(png_contents)
#         self.assertIsNotNone(jpg_contents)
#         self.assertEqual(png_contents, self.test_png.data)
#         self.assertEqual(jpg_contents, self.test_jpg.data)
#
#
