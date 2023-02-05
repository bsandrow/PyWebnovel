from unittest import TestCase

from webnovel.data import Image, Person
from webnovel.epub.data import EpubNovel
from webnovel.epub.files import CoverPage, TitlePage, EpubImage, Stylesheet
from webnovel.epub.pkg import EpubPackage

from ...helpers import get_test_data


class StylesheetsTestCase(TestCase):



class TitlePageTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.test_png = Image(
            url="file:///test-image.png",
            data=get_test_data("test-image.png", use_bytes=True),
            mimetype="image/png",
            did_load=True,
        )
        cls.test_jpg = Image(
            url="file:///test-image.jpg",
            data=get_test_data("test-image.jpg", use_bytes=True),
            mimetype="image/jpg",
            did_load=True,
        )

    def test_generate(self):
        pkg = EpubPackage(
            filename="test.epub",
            novel=EpubNovel(
                url="https://example.com/novel/my-test-novel/",
                title="My Test Novel",
                author=Person(name="Johnny B. Goode"),
            ),
        )
        title_page = TitlePage(pkg)
        title_page.generate()
        self.assertEqual(
            title_page.data,
            (
                b"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
                b"<html xmlns=\"http://www.w3.org/1999/xhtml\">\n"
                b"  <head>\n"
                b"    <title>My Test Novel by Johnny B. Goode</title>\n"
                b"    <link href=\"stylesheet.css\" type=\"text/css\" rel=\"stylesheet\"/>\n"
                b"  </head>\n"
                b"  <body class=\"pywebnovel-titlepage\">\n"
                b"    <h3><a href=\"https://example.com/novel/my-test-novel/\">My Test Novel</a> by Johnny B. Goode</h3>\n"
                b"    <div><br /></div>\n"
                b"  </body>\n"
                b"</html>"
            )
        )


class CoverPageTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.test_png = Image(
            url="file:///test-image.png",
            data=get_test_data("test-image.png", use_bytes=True),
            mimetype="image/png",
            did_load=True,
        )
        cls.test_jpg = Image(
            url="file:///test-image.jpg",
            data=get_test_data("test-image.jpg", use_bytes=True),
            mimetype="image/jpg",
            did_load=True,
        )

    def test_generate(self):
        epub_image = EpubImage.from_image(self.test_png, image_id="abc123")
        cover_page = CoverPage()
        cover_page.generate(cover_image=epub_image)
        self.assertEqual(
            cover_page.data,
            (
                b"<html xmlns=\"http://www.w3.org/1999/xhtml\" xml:lang=\"en\">\n"
                b"<head>\n"
                b"  <title>Cover</title>\n"
                b"  <style type=\"text/css\" title=\"override_css\">\n"
                b"    @page { padding: 0pt; margin: 0pt }\n"
                b"    body { text-align: center; padding: 0pt; margin: 0pt; }\n"
                b"    div { margin: 0pt; padding: 0pt; }\n"
                b"  </style>\n"
                b"</head>\n"
                b"<body class=\"fff_coverpage\">\n"
                b"  <div><img src=\"OEBPS/abc123.png\" alt=\"cover\"/></div>\n"
                b"</body>\n"
                b"</html>"
            )
        )
