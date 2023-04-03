import datetime
from pathlib import Path
import pkgutil
from unittest import TestCase, mock

from bs4 import BeautifulSoup
import freezegun

from webnovel.data import Chapter, Image, Person
from webnovel.epub import EpubPackage, files


class MetadataFileTestCase(TestCase):
    def test_generate(self):
        self.assertEqual(files.MimetypeFile().generate(pkg=None), b"application/epub+zip")

    def test_from_dict(self):
        expected = files.MimetypeFile()
        actual = files.MimetypeFile.from_dict({"file_id": "mimetype", "filename": "mimetype"})
        self.assertEqual(actual, expected)


class ContainerXMLTestCase(TestCase):
    def test_generate(self):
        self.assertEqual(
            files.ContainerXML().generate(pkg=None),
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
        expected = files.ContainerXML()
        actual = files.ContainerXML.from_dict({"file_id": "container-xml", "filename": "META-INF/container.xml"})
        self.assertEqual(actual, expected)

    def test_to_dict(self):
        expected = {"file_id": "container-xml", "filename": "META-INF/container.xml", "mimetype": "", "title": None}
        actual = files.ContainerXML().to_dict()
        self.assertEqual(actual, expected)


class StylesheetTestCase(TestCase):
    def test_generate(self):
        pkg = mock.Mock()
        pkg.extra_css = None
        actual = files.Stylesheet().generate(pkg)
        expected = pkgutil.get_data("webnovel.epub", "content/stylesheet.css")
        self.assertEqual(actual, expected)

    def test_from_dict(self):
        expected = files.Stylesheet()
        actual = files.Stylesheet.from_dict({"file_id": "style", "filename": "OEBPS/stylesheet.css"})
        self.assertEqual(actual, expected)

    def test_to_dict(self):
        expected = {"file_id": "style", "filename": "OEBPS/stylesheet.css", "mimetype": "text/css", "title": None}
        actual = files.Stylesheet().to_dict()
        self.assertEqual(actual, expected)


class GenerateToCListTestCase(TestCase):
    def test_full_list(self):
        pkg = mock.Mock()
        pkg.cover_page = object()
        pkg.title_page = object()
        pkg.toc_page = object()
        ch1 = mock.Mock()
        ch1.file_id = "010"
        ch2 = mock.Mock()
        ch2.file_id = "009"
        pkg.chapter_files = [ch1, ch2]
        actual = files.generate_toc_list(pkg)
        expected = [pkg.cover_page, pkg.title_page, pkg.toc_page, ch2, ch1]
        self.assertEqual(actual, expected)

    def test_missing_cover_page(self):
        pkg = mock.Mock()
        pkg.cover_page = None
        pkg.title_page = object()
        pkg.toc_page = object()
        ch1 = mock.Mock()
        ch1.file_id = "010"
        ch2 = mock.Mock()
        ch2.file_id = "009"
        pkg.chapter_files = [ch1, ch2]
        actual = files.generate_toc_list(pkg)
        expected = [pkg.title_page, pkg.toc_page, ch2, ch1]
        self.assertEqual(actual, expected)

    def test_missing_toc_page(self):
        pkg = mock.Mock()
        pkg.cover_page = object()
        pkg.title_page = object()
        pkg.toc_page = None
        ch1 = mock.Mock()
        ch1.file_id = "010"
        ch2 = mock.Mock()
        ch2.file_id = "009"
        pkg.chapter_files = [ch1, ch2]
        actual = files.generate_toc_list(pkg)
        expected = [pkg.cover_page, pkg.title_page, ch2, ch1]
        self.assertEqual(actual, expected)

    def test_missing_title_page(self):
        pkg = mock.Mock()
        pkg.cover_page = object()
        pkg.title_page = None
        pkg.toc_page = object()
        ch1 = mock.Mock()
        ch1.file_id = "010"
        ch2 = mock.Mock()
        ch2.file_id = "009"
        pkg.chapter_files = [ch1, ch2]
        actual = files.generate_toc_list(pkg)
        expected = [pkg.cover_page, pkg.toc_page, ch2, ch1]
        self.assertEqual(actual, expected)


class ImageFileTestCase(TestCase):
    def test_init_handles_missing_extension(self):
        img = files.ImageFile(file_id="FILE-001", mimetype="image/gif")
        self.assertEqual(img.filename, "OEBPS/Images/FILE-001.gif")

    def test_init_uses_passed_extension(self):
        img = files.ImageFile(file_id="FILE-001", mimetype="image/gif", extension=".test")
        self.assertEqual(img.filename, "OEBPS/Images/FILE-001.test")

    def test_from_dict(self):
        actual = files.ImageFile.from_dict({"file_id": "FILE-002", "mimetype": "image/gif", "filename": "my-image.jpg"})
        expected = files.ImageFile(file_id="FILE-002", mimetype="image/gif", filename="my-image.jpg")
        self.assertEqual(actual, expected)

    def test_to_dict(self):
        expected = {"file_id": "FILE-002", "mimetype": "image/gif", "filename": "my-image.jpg", "is_cover_image": False}
        actual = files.ImageFile(file_id="FILE-002", mimetype="image/gif", filename="my-image.jpg").to_dict()
        self.assertEqual(actual, expected)

    def test_generate(self):
        img = files.ImageFile(file_id="FILE-002", mimetype="image/gif", filename="my-image.jpg")
        expected = object()
        pkg = mock.Mock()
        pkg.image_map = {"FILE-002": expected}
        actual = img.generate(pkg)
        self.assertEqual(actual, expected)


class NavigationControlFileTestCase(TestCase):
    def test_generate(self):
        pkg = EpubPackage(
            options={},
            metadata={"novel_url": ":URL:", "site_id": ":SITE_ID:", "novel_id": ":NOVEL_ID:", "title": ":TITLE:"},
        )
        actual = files.NavigationControlFile().generate(pkg)
        expected = (
            (
                '<?xml version="1.0" encoding="utf-8"?>'
                '<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">'
                "<head>"
                '<meta name="dtb:uid" content="urn:pywebnovel:uid:{site_id}:{novel_id}"/>'
                '<meta name="dtb:depth" content="1"/>'
                '<meta name="dtb:totalPageCount" content="0"/>'
                '<meta name="dtb:maxPageNumber" content="0"/>'
                "</head>"
                "<docTitle>"
                "<text>{novel_title}</text>"
                "</docTitle>"
                "<navMap>"
                '<navPoint id="{title_page_id}" playOrder="0"><navLabel><text>{title_page_title}</text></navLabel><content src="{title_page_path}"/></navPoint>'
                '<navPoint id="{toc_page_id}" playOrder="1"><navLabel><text>{toc_page_title}</text></navLabel><content src="{toc_page_path}"/></navPoint>'
                "</navMap>"
                "</ncx>"
            )
            .format(
                **{
                    "title_page_id": pkg.title_page.file_id,
                    "title_page_title": pkg.title_page.title,
                    "title_page_path": pkg.title_page.relative_to(pkg.ncx.parent),
                    "toc_page_id": pkg.toc_page.file_id,
                    "toc_page_title": pkg.toc_page.title,
                    "toc_page_path": pkg.toc_page.relative_to(pkg.ncx.parent),
                    "site_id": pkg.metadata.site_id,
                    "novel_id": pkg.metadata.novel_id,
                    "novel_title": pkg.metadata.title,
                }
            )
            .encode("utf-8")
        )
        self.assertEqual(actual, expected)

    def test_generate_handles_cover_page(self):
        pkg = EpubPackage(
            options={"include_toc_page": False},
            metadata={"novel_url": ":URL:", "site_id": ":SITE_ID:", "novel_id": ":NOVEL_ID:", "title": ":TITLE:"},
        )
        img = Image(
            url="https://example.com/imgs/novel-cover.jpg", mimetype="image/jpg", did_load=True, data=b":IMGDATA:"
        )
        pkg.add_image(img, content=img.data, is_cover_image=True)
        actual = files.NavigationControlFile().generate(pkg)
        expected = (
            (
                '<?xml version="1.0" encoding="utf-8"?>'
                '<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">'
                "<head>"
                '<meta name="dtb:uid" content="urn:pywebnovel:uid:{site_id}:{novel_id}"/>'
                '<meta name="dtb:depth" content="1"/>'
                '<meta name="dtb:totalPageCount" content="0"/>'
                '<meta name="dtb:maxPageNumber" content="0"/>'
                "</head>"
                "<docTitle>"
                "<text>{novel_title}</text>"
                "</docTitle>"
                "<navMap>"
                '<navPoint id="{cover_page_id}" playOrder="0"><navLabel><text>{cover_page_title}</text></navLabel><content src="{cover_page_path}"/></navPoint>'
                '<navPoint id="{title_page_id}" playOrder="1"><navLabel><text>{title_page_title}</text></navLabel><content src="{title_page_path}"/></navPoint>'
                "</navMap>"
                "</ncx>"
            )
            .format(
                **{
                    "cover_page_id": pkg.cover_page.file_id,
                    "cover_page_title": pkg.cover_page.title,
                    "cover_page_path": pkg.cover_page.relative_to(pkg.ncx.parent),
                    "title_page_id": pkg.title_page.file_id,
                    "title_page_title": pkg.title_page.title,
                    "title_page_path": pkg.title_page.relative_to(pkg.ncx.parent),
                    "site_id": pkg.metadata.site_id,
                    "novel_id": pkg.metadata.novel_id,
                    "novel_title": pkg.metadata.title,
                }
            )
            .encode("utf-8")
        )
        self.assertEqual(actual, expected)

    def test_generate_handles_missing_toc_page(self):
        pkg = EpubPackage(
            options={"include_toc_page": False},
            metadata={"novel_url": ":URL:", "site_id": ":SITE_ID:", "novel_id": ":NOVEL_ID:", "title": ":TITLE:"},
        )
        actual = files.NavigationControlFile().generate(pkg)
        expected = (
            (
                '<?xml version="1.0" encoding="utf-8"?>'
                '<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">'
                "<head>"
                '<meta name="dtb:uid" content="urn:pywebnovel:uid:{site_id}:{novel_id}"/>'
                '<meta name="dtb:depth" content="1"/>'
                '<meta name="dtb:totalPageCount" content="0"/>'
                '<meta name="dtb:maxPageNumber" content="0"/>'
                "</head>"
                "<docTitle>"
                "<text>{novel_title}</text>"
                "</docTitle>"
                "<navMap>"
                '<navPoint id="{title_page_id}" playOrder="0"><navLabel><text>{title_page_title}</text></navLabel><content src="{title_page_path}"/></navPoint>'
                "</navMap>"
                "</ncx>"
            )
            .format(
                **{
                    "title_page_id": pkg.title_page.file_id,
                    "title_page_title": pkg.title_page.title,
                    "title_page_path": pkg.title_page.relative_to(pkg.ncx.parent),
                    "site_id": pkg.metadata.site_id,
                    "novel_id": pkg.metadata.novel_id,
                    "novel_title": pkg.metadata.title,
                }
            )
            .encode("utf-8")
        )
        self.assertEqual(actual, expected)

    def test_generate_handles_missing_title_page(self):
        pkg = EpubPackage(
            options={"include_title_page": False},
            metadata={"novel_url": ":URL:", "site_id": ":SITE_ID:", "novel_id": ":NOVEL_ID:", "title": ":TITLE:"},
        )
        actual = files.NavigationControlFile().generate(pkg)
        expected = (
            (
                '<?xml version="1.0" encoding="utf-8"?>'
                '<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">'
                "<head>"
                '<meta name="dtb:uid" content="urn:pywebnovel:uid:{site_id}:{novel_id}"/>'
                '<meta name="dtb:depth" content="1"/>'
                '<meta name="dtb:totalPageCount" content="0"/>'
                '<meta name="dtb:maxPageNumber" content="0"/>'
                "</head>"
                "<docTitle>"
                "<text>{novel_title}</text>"
                "</docTitle>"
                "<navMap>"
                '<navPoint id="{toc_page_id}" playOrder="0"><navLabel><text>{toc_page_title}</text></navLabel><content src="{toc_page_path}"/></navPoint>'
                "</navMap>"
                "</ncx>"
            )
            .format(
                **{
                    "toc_page_id": pkg.toc_page.file_id,
                    "toc_page_title": pkg.toc_page.title,
                    "toc_page_path": pkg.toc_page.relative_to(pkg.ncx.parent),
                    "site_id": pkg.metadata.site_id,
                    "novel_id": pkg.metadata.novel_id,
                    "novel_title": pkg.metadata.title,
                }
            )
            .encode("utf-8")
        )
        self.assertEqual(actual, expected)

    def test_generate_includes_chapters(self):
        pkg = EpubPackage(
            options={"include_title_page": False},
            metadata={"novel_url": ":URL:", "site_id": ":SITE_ID:", "novel_id": ":NOVEL_ID:", "title": ":TITLE:"},
        )
        pkg.add_chapter(Chapter(url="http://example.come/chapter-2", chapter_no=2, title="Chapter 2. Example 2"))
        pkg.add_chapter(Chapter(url="http://example.come/chapter-1", chapter_no=1, title="Chapter 1. Example 1"))
        actual = files.NavigationControlFile().generate(pkg)
        expected = (
            (
                '<?xml version="1.0" encoding="utf-8"?>'
                '<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">'
                "<head>"
                '<meta name="dtb:uid" content="urn:pywebnovel:uid:{site_id}:{novel_id}"/>'
                '<meta name="dtb:depth" content="1"/>'
                '<meta name="dtb:totalPageCount" content="0"/>'
                '<meta name="dtb:maxPageNumber" content="0"/>'
                "</head>"
                "<docTitle>"
                "<text>{novel_title}</text>"
                "</docTitle>"
                "<navMap>"
                '<navPoint id="{toc_page_id}" playOrder="0"><navLabel><text>{toc_page_title}</text></navLabel><content src="{toc_page_path}"/></navPoint>'
                '<navPoint id="{chapter_1_id}" playOrder="1"><navLabel><text>{chapter_1_title}</text></navLabel><content src="{chapter_1_path}"/></navPoint>'
                '<navPoint id="{chapter_2_id}" playOrder="2"><navLabel><text>{chapter_2_title}</text></navLabel><content src="{chapter_2_path}"/></navPoint>'
                "</navMap>"
                "</ncx>"
            )
            .format(
                **{
                    "chapter_1_id": pkg.chapter_files[0].file_id,
                    "chapter_1_title": pkg.chapter_files[0].title,
                    "chapter_1_path": pkg.chapter_files[0].relative_to(pkg.ncx.parent),
                    "chapter_2_id": pkg.chapter_files[1].file_id,
                    "chapter_2_title": pkg.chapter_files[1].title,
                    "chapter_2_path": pkg.chapter_files[1].relative_to(pkg.ncx.parent),
                    "toc_page_id": pkg.toc_page.file_id,
                    "toc_page_title": pkg.toc_page.title,
                    "toc_page_path": pkg.toc_page.relative_to(pkg.ncx.parent),
                    "site_id": pkg.metadata.site_id,
                    "novel_id": pkg.metadata.novel_id,
                    "novel_title": pkg.metadata.title,
                }
            )
            .encode("utf-8")
        )
        self.assertEqual(pkg.chapter_files[0].title, "Chapter 2. Example 2")
        self.assertEqual(actual, expected)


class TitlePageTestCase(TestCase):
    @freezegun.freeze_time("2001-01-01 12:15")
    def test_generate(self):
        pkg = EpubPackage(
            options={},
            metadata={"novel_url": ":URL:", "site_id": ":SITE_ID:", "novel_id": ":NOVEL_ID:", "title": ":TITLE:"},
        )
        actual = files.TitlePage().generate(pkg)
        expected = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml">\n'
            f"  <head>\n"
            f"    <title>{pkg.metadata.title}</title>\n"
            f'    <link href="{pkg.stylesheet.relative_to(pkg.title_page.parent)}" type="text/css" rel="stylesheet"/>\n'
            f"  </head>\n"
            f'  <body class="pywebnovel-titlepage">\n'
            f'    <h3 class="pywn_title-page-title"><a href="">{pkg.metadata.title}</a></h3>\n'
            f'    <div class="pywn_information-section">\n'
            f"        <h4> --[ Information ]-- </h4>\n"
            f"        \n"
            f'          <span class="pywn_information-block"><strong>Publisher:</strong> {pkg.metadata.site_id}</span>\n'
            f"        \n"
            f'          <span class="pywn_information-block"><strong>Chapter Count:</strong> {len(pkg.chapters)}</span>\n'
            f"        \n"
            f'          <span class="pywn_information-block"><strong>Status:</strong> {pkg.metadata.status.value}</span>\n'
            f"        </div>\n"
            f'    <div class="pywn_bottom-info">\n'
            f"      <div>Scraped from {pkg.metadata.site_id}.</div>\n"
            f"      <div>Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>\n"
            f"    </div>\n"
            f"  </body>\n"
            f"</html>"
        ).encode("utf-8")
        self.assertEqual(actual, expected)

    @freezegun.freeze_time("2001-01-01 12:15")
    def test_with_author_name_only(self):
        pkg = EpubPackage(
            options={},
            metadata={
                "novel_url": ":URL:",
                "site_id": ":SITE_ID:",
                "novel_id": ":NOVEL_ID:",
                "title": ":TITLE:",
                "author": {"name": ":AUTHORNAME:"},
            },
        )
        actual = files.TitlePage().generate(pkg)
        expected = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml">\n'
            f"  <head>\n"
            f"    <title>{pkg.metadata.title}</title>\n"
            f'    <link href="{pkg.stylesheet.relative_to(pkg.title_page.parent)}" type="text/css" rel="stylesheet"/>\n'
            f"  </head>\n"
            f'  <body class="pywebnovel-titlepage">\n'
            f'    <h3 class="pywn_title-page-title"><a href="">{pkg.metadata.title}</a></h3>\n'
            f'    <div class="pywn_credits-section">\n'
            f"        <h4> --[ Credits ]-- </h4>\n"
            f"        \n"
            f"          <p>\n"
            f"            <strong>Author: </strong>{pkg.metadata.author.name}\n"
            f"            </p>\n"
            f"        \n"
            f"    </div>\n"
            f'    <div class="pywn_information-section">\n'
            f"        <h4> --[ Information ]-- </h4>\n"
            f"        \n"
            f'          <span class="pywn_information-block"><strong>Publisher:</strong> {pkg.metadata.site_id}</span>\n'
            f"        \n"
            f'          <span class="pywn_information-block"><strong>Chapter Count:</strong> {len(pkg.chapters)}</span>\n'
            f"        \n"
            f'          <span class="pywn_information-block"><strong>Status:</strong> {pkg.metadata.status.value}</span>\n'
            f"        </div>\n"
            f'    <div class="pywn_bottom-info">\n'
            f"      <div>Scraped from {pkg.metadata.site_id}.</div>\n"
            f"      <div>Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>\n"
            f"    </div>\n"
            f"  </body>\n"
            f"</html>"
        ).encode("utf-8")
        self.assertEqual(actual, expected)

    @freezegun.freeze_time("2001-01-01 12:15")
    def test_with_author_name_and_email(self):
        pkg = EpubPackage(
            options={},
            metadata={
                "novel_url": ":URL:",
                "site_id": ":SITE_ID:",
                "novel_id": ":NOVEL_ID:",
                "title": ":TITLE:",
                "author": {"name": ":AUTHORNAME:", "email": "author@example.com"},
            },
        )
        actual = files.TitlePage().generate(pkg)
        expected = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml">\n'
            f"  <head>\n"
            f"    <title>{pkg.metadata.title}</title>\n"
            f'    <link href="{pkg.stylesheet.relative_to(pkg.title_page.parent)}" type="text/css" rel="stylesheet"/>\n'
            f"  </head>\n"
            f'  <body class="pywebnovel-titlepage">\n'
            f'    <h3 class="pywn_title-page-title"><a href="">{pkg.metadata.title}</a></h3>\n'
            f'    <div class="pywn_credits-section">\n'
            f"        <h4> --[ Credits ]-- </h4>\n"
            f"        \n"
            f"          <p>\n"
            f"            <strong>Author: </strong>{pkg.metadata.author.name} &lt;author@example.com&gt;\n"
            f"            </p>\n"
            f"        \n"
            f"    </div>\n"
            f'    <div class="pywn_information-section">\n'
            f"        <h4> --[ Information ]-- </h4>\n"
            f"        \n"
            f'          <span class="pywn_information-block"><strong>Publisher:</strong> {pkg.metadata.site_id}</span>\n'
            f"        \n"
            f'          <span class="pywn_information-block"><strong>Chapter Count:</strong> {len(pkg.chapters)}</span>\n'
            f"        \n"
            f'          <span class="pywn_information-block"><strong>Status:</strong> {pkg.metadata.status.value}</span>\n'
            f"        </div>\n"
            f'    <div class="pywn_bottom-info">\n'
            f"      <div>Scraped from {pkg.metadata.site_id}.</div>\n"
            f"      <div>Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>\n"
            f"    </div>\n"
            f"  </body>\n"
            f"</html>"
        ).encode("utf-8")
        self.assertEqual(actual, expected)

    @freezegun.freeze_time("2001-01-01 12:15")
    def test_with_author_with_name_and_url(self):
        pkg = EpubPackage(
            options={},
            metadata={
                "novel_url": ":URL:",
                "site_id": ":SITE_ID:",
                "novel_id": ":NOVEL_ID:",
                "title": ":TITLE:",
                "author": {"name": ":AUTHORNAME:", "url": "https://example.com/:author:"},
            },
        )
        actual = files.TitlePage().generate(pkg)
        expected = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml">\n'
            f"  <head>\n"
            f"    <title>{pkg.metadata.title}</title>\n"
            f'    <link href="{pkg.stylesheet.relative_to(pkg.title_page.parent)}" type="text/css" rel="stylesheet"/>\n'
            f"  </head>\n"
            f'  <body class="pywebnovel-titlepage">\n'
            f'    <h3 class="pywn_title-page-title"><a href="">{pkg.metadata.title}</a></h3>\n'
            f'    <div class="pywn_credits-section">\n'
            f"        <h4> --[ Credits ]-- </h4>\n"
            f"        \n"
            f"          <p>\n"
            f"            <strong>Author: </strong>\n"
            f'              <a href="{pkg.metadata.author.url}">\n'
            f"                :AUTHORNAME:\n"
            f"              </a></p>\n"
            f"        \n"
            f"    </div>\n"
            f'    <div class="pywn_information-section">\n'
            f"        <h4> --[ Information ]-- </h4>\n"
            f"        \n"
            f'          <span class="pywn_information-block"><strong>Publisher:</strong> {pkg.metadata.site_id}</span>\n'
            f"        \n"
            f'          <span class="pywn_information-block"><strong>Chapter Count:</strong> {len(pkg.chapters)}</span>\n'
            f"        \n"
            f'          <span class="pywn_information-block"><strong>Status:</strong> {pkg.metadata.status.value}</span>\n'
            f"        </div>\n"
            f'    <div class="pywn_bottom-info">\n'
            f"      <div>Scraped from {pkg.metadata.site_id}.</div>\n"
            f"      <div>Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>\n"
            f"    </div>\n"
            f"  </body>\n"
            f"</html>"
        ).encode("utf-8")
        self.assertEqual(actual, expected)

    @freezegun.freeze_time("2001-01-01 12:15")
    def test_generate_with_tags(self):
        pkg = EpubPackage(
            options={},
            metadata={
                "novel_url": ":URL:",
                "site_id": ":SITE_ID:",
                "novel_id": ":NOVEL_ID:",
                "title": ":TITLE:",
                "tags": ["tag1", "tag2"],
            },
        )
        actual = files.TitlePage().generate(pkg)
        expected = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml">\n'
            f"  <head>\n"
            f"    <title>{pkg.metadata.title}</title>\n"
            f'    <link href="{pkg.stylesheet.relative_to(pkg.title_page.parent)}" type="text/css" rel="stylesheet"/>\n'
            f"  </head>\n"
            f'  <body class="pywebnovel-titlepage">\n'
            f'    <h3 class="pywn_title-page-title"><a href="">{pkg.metadata.title}</a></h3>\n'
            f'    <div class="pywn_information-section">\n'
            f"        <h4> --[ Information ]-- </h4>\n"
            f"        \n"
            f'          <span class="pywn_information-block"><strong>Publisher:</strong> {pkg.metadata.site_id}</span>\n'
            f"        \n"
            f'          <span class="pywn_information-block"><strong>Chapter Count:</strong> {len(pkg.chapters)}</span>\n'
            f"        \n"
            f'          <span class="pywn_information-block"><strong>Status:</strong> {pkg.metadata.status.value}</span>\n'
            f"        </div>\n"
            f'    <div class="pywn_bottom-info">\n'
            f"      <div>Scraped from {pkg.metadata.site_id}.</div>\n"
            f"      <div>Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>\n"
            f"    </div>\n"
            f"  </body>\n"
            f"</html>"
        ).encode("utf-8")
        self.assertEqual(actual, expected)


class CoverPageTestCase(TestCase):
    def test_generate_cover_page(self):
        pkg = EpubPackage(
            options={},
            metadata={"novel_url": ":URL:", "site_id": ":SITE_ID:", "novel_id": ":NOVEL_ID:", "title": ":TITLE:"},
        )
        img = Image(
            url="https://example.com/imgs/novel-cover.jpg", mimetype="image/jpg", did_load=True, data=b":IMGDATA:"
        )
        pkg.add_image(img, content=img.data, is_cover_image=True)

        self.assertIsInstance(pkg.cover_page, files.CoverPage)

        actual = pkg.cover_page.generate(pkg)
        expected = (
            f'<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">\n'
            f"<head>\n"
            f"  <title>{pkg.cover_page.title}</title>\n"
            f'  <style type="text/css" title="override_css">\n'
            "    @page { padding: 0pt; margin: 0pt }\n"
            "    body { text-align: center; padding: 0pt; margin: 0pt; }\n"
            "    div { margin: 0pt; padding: 0pt; }\n"
            f"  </style>\n"
            f"</head>\n"
            f'<body class="pywebnovel_cover_page">\n'
            f'  <div><img src="{pkg.cover_image.relative_to(pkg.cover_page.parent)}" alt="cover"/></div>\n'
            f"</body>\n"
            f"</html>"
        ).encode("utf-8")

        self.assertEqual(actual, expected)


class NavXhtmlTestCase(TestCase):
    def test_generate_with_cover_page(self):
        pkg = EpubPackage(
            options={},
            metadata={"novel_url": ":URL:", "site_id": ":SITE_ID:", "novel_id": ":NOVEL_ID:", "title": ":TITLE:"},
        )
        img = Image(
            url="https://example.com/imgs/novel-cover.jpg", mimetype="image/jpg", did_load=True, data=b":IMGDATA:"
        )
        pkg.add_image(img, content=img.data, is_cover_image=True)

        actual = pkg.nav.generate(pkg)
        expected = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">\n'
            f"<head>\n"
            f"  <title>Navigation</title>\n"
            f'  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n'
            f"</head>\n"
            f"<body>\n"
            f'  <nav epub:type="toc">\n'
            f"    <ol>\n"
            f"      \n"
            f"      <li>\n"
            f'        <a href="{pkg.cover_page.relative_to(pkg.nav.parent)}">{pkg.cover_page.title}</a>\n'
            f"      </li>\n"
            f"      \n"
            f"      <li>\n"
            f'        <a href="{pkg.title_page.relative_to(pkg.nav.parent)}">{pkg.title_page.title}</a>\n'
            f"      </li>\n"
            f"      \n"
            f"      <li>\n"
            f'        <a href="{pkg.toc_page.relative_to(pkg.nav.parent)}">{pkg.toc_page.title}</a>\n'
            f"      </li>\n"
            f"      \n"
            f"    </ol>\n"
            f"  </nav>\n"
            f'  <nav epub:type="landmarks" hidden="">\n'
            f"    <ol>\n"
            f"      <li>\n"
            f'        <a href="{pkg.cover_page.relative_to(pkg.nav.parent)}" epub:type="cover">Cover</a>\n'
            f"      </li>\n"
            f"    </ol>\n"
            f"  </nav>\n"
            f"</body>\n"
            f"</html>"
        ).encode("utf-8")

        self.assertEqual(actual, expected)

    def test_generate_without_cover_page(self):
        pkg = EpubPackage(
            options={},
            metadata={"novel_url": ":URL:", "site_id": ":SITE_ID:", "novel_id": ":NOVEL_ID:", "title": ":TITLE:"},
        )
        self.assertIsNone(pkg.cover_page)

        actual = pkg.nav.generate(pkg)
        expected = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">\n'
            f"<head>\n"
            f"  <title>Navigation</title>\n"
            f'  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n'
            f"</head>\n"
            f"<body>\n"
            f'  <nav epub:type="toc">\n'
            f"    <ol>\n"
            f"      \n"
            f"      <li>\n"
            f'        <a href="{pkg.title_page.relative_to(pkg.nav.parent)}">{pkg.title_page.title}</a>\n'
            f"      </li>\n"
            f"      \n"
            f"      <li>\n"
            f'        <a href="{pkg.toc_page.relative_to(pkg.nav.parent)}">{pkg.toc_page.title}</a>\n'
            f"      </li>\n"
            f"      \n"
            f"    </ol>\n"
            f"  </nav>\n"
            f'  <nav epub:type="landmarks" hidden="">\n'
            f"    <ol></ol>\n"
            f"  </nav>\n"
            f"</body>\n"
            f"</html>"
        ).encode("utf-8")

        self.assertEqual(actual, expected)

    def test_generate_with_chapters(self):
        pkg = EpubPackage(
            options={},
            metadata={"novel_url": ":URL:", "site_id": ":SITE_ID:", "novel_id": ":NOVEL_ID:", "title": ":TITLE:"},
        )
        img = Image(
            url="https://example.com/imgs/novel-cover.jpg", mimetype="image/jpg", did_load=True, data=b":IMGDATA:"
        )
        pkg.add_image(img, content=img.data, is_cover_image=True)
        pkg.add_chapter(Chapter(url="http://example.come/chapter-2", chapter_no=2, title="Chapter 2. Example 2"))
        pkg.add_chapter(Chapter(url="http://example.come/chapter-1", chapter_no=1, title="Chapter 1. Example 1"))

        actual = pkg.nav.generate(pkg)
        expected = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">\n'
            f"<head>\n"
            f"  <title>Navigation</title>\n"
            f'  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n'
            f"</head>\n"
            f"<body>\n"
            f'  <nav epub:type="toc">\n'
            f"    <ol>\n"
            f"      \n"
            f"      <li>\n"
            f'        <a href="{pkg.cover_page.relative_to(pkg.nav.parent)}">{pkg.cover_page.title}</a>\n'
            f"      </li>\n"
            f"      \n"
            f"      <li>\n"
            f'        <a href="{pkg.title_page.relative_to(pkg.nav.parent)}">{pkg.title_page.title}</a>\n'
            f"      </li>\n"
            f"      \n"
            f"      <li>\n"
            f'        <a href="{pkg.toc_page.relative_to(pkg.nav.parent)}">{pkg.toc_page.title}</a>\n'
            f"      </li>\n"
            f"      \n"
            f"      <li>\n"
            f'        <a href="{pkg.chapter_files[0].relative_to(pkg.nav.parent)}">{pkg.chapter_files[0].title}</a>\n'
            f"      </li>\n"
            f"      \n"
            f"      <li>\n"
            f'        <a href="{pkg.chapter_files[1].relative_to(pkg.nav.parent)}">{pkg.chapter_files[1].title}</a>\n'
            f"      </li>\n"
            f"      \n"
            f"    </ol>\n"
            f"  </nav>\n"
            f'  <nav epub:type="landmarks" hidden="">\n'
            f"    <ol>\n"
            f"      <li>\n"
            f'        <a href="{pkg.cover_page.relative_to(pkg.nav.parent)}" epub:type="cover">Cover</a>\n'
            f"      </li>\n"
            f"    </ol>\n"
            f"  </nav>\n"
            f"</body>\n"
            f"</html>"
        ).encode("utf-8")

        print(f"{actual!r}")
        print("----")
        print(f"{expected!r}")

        self.assertEqual(actual, expected)


class TableOfContentsTestCase(TestCase):
    def test_generate(self):
        pkg = EpubPackage(
            options={},
            metadata={"novel_url": ":URL:", "site_id": ":SITE_ID:", "novel_id": ":NOVEL_ID:", "title": ":TITLE:"},
        )
        img = Image(
            url="https://example.com/imgs/novel-cover.jpg", mimetype="image/jpg", did_load=True, data=b":IMGDATA:"
        )
        pkg.add_image(img, content=img.data, is_cover_image=True)
        pkg.add_chapter(Chapter(url="http://example.come/chapter-2", chapter_no=2, title="Chapter 2. Example 2"))
        pkg.add_chapter(Chapter(url="http://example.come/chapter-1", chapter_no=1, title="Chapter 1. Example 1"))

        actual = pkg.toc_page.generate(pkg)
        expected = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml">\n'
            f"  <head>\n"
            f"    <title>{pkg.metadata.title}</title>\n"
            f'    <link href="{pkg.stylesheet.relative_to(pkg.toc_page.parent)}" type="text/css" rel="stylesheet"/>\n'
            f"  </head>\n"
            f'  <body class="pywn-toc-page">\n'
            f"    <div>\n"
            f"      <h3>Table of Contents</h3>\n"
            f"      \n"
            f'        <a href="{pkg.cover_page.relative_to(pkg.toc_page.parent)}">{pkg.cover_page.title}</a><br />\n'
            f"      \n"
            f'        <a href="{pkg.title_page.relative_to(pkg.toc_page.parent)}">{pkg.title_page.title}</a><br />\n'
            f"      \n"
            f'        <a href="{pkg.toc_page.relative_to(pkg.toc_page.parent)}">{pkg.toc_page.title}</a><br />\n'
            f"      \n"
            f'        <a href="{pkg.chapter_files[0].relative_to(pkg.toc_page.parent)}">{pkg.chapter_files[0].title}</a><br />\n'
            f"      \n"
            f'        <a href="{pkg.chapter_files[1].relative_to(pkg.toc_page.parent)}">{pkg.chapter_files[1].title}</a><br />\n'
            f"      \n"
            f"    </div>\n"
            f"  </body>\n"
            f"</html>"
        ).encode("utf-8")

        print(f"{actual!r}")

        self.assertEqual(actual, expected)

    def test_generate_with_author(self):
        pkg = EpubPackage(
            options={},
            metadata={"novel_url": ":URL:", "site_id": ":SITE_ID:", "novel_id": ":NOVEL_ID:", "title": ":TITLE:"},
        )
        pkg.metadata.author = Person(name="Mae Floy")
        img = Image(
            url="https://example.com/imgs/novel-cover.jpg", mimetype="image/jpg", did_load=True, data=b":IMGDATA:"
        )
        pkg.add_image(img, content=img.data, is_cover_image=True)
        pkg.add_chapter(Chapter(url="http://example.come/chapter-2", chapter_no=2, title="Chapter 2. Example 2"))
        pkg.add_chapter(Chapter(url="http://example.come/chapter-1", chapter_no=1, title="Chapter 1. Example 1"))

        actual = pkg.toc_page.generate(pkg)
        expected = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml">\n'
            f"  <head>\n"
            f"    <title>{pkg.metadata.title} by {pkg.metadata.author.name}</title>\n"
            f'    <link href="{pkg.stylesheet.relative_to(pkg.toc_page.parent)}" type="text/css" rel="stylesheet"/>\n'
            f"  </head>\n"
            f'  <body class="pywn-toc-page">\n'
            f"    <div>\n"
            f"      <h3>Table of Contents</h3>\n"
            f"      \n"
            f'        <a href="{pkg.cover_page.relative_to(pkg.toc_page.parent)}">{pkg.cover_page.title}</a><br />\n'
            f"      \n"
            f'        <a href="{pkg.title_page.relative_to(pkg.toc_page.parent)}">{pkg.title_page.title}</a><br />\n'
            f"      \n"
            f'        <a href="{pkg.toc_page.relative_to(pkg.toc_page.parent)}">{pkg.toc_page.title}</a><br />\n'
            f"      \n"
            f'        <a href="{pkg.chapter_files[0].relative_to(pkg.toc_page.parent)}">{pkg.chapter_files[0].title}</a><br />\n'
            f"      \n"
            f'        <a href="{pkg.chapter_files[1].relative_to(pkg.toc_page.parent)}">{pkg.chapter_files[1].title}</a><br />\n'
            f"      \n"
            f"    </div>\n"
            f"  </body>\n"
            f"</html>"
        ).encode("utf-8")

        print(f"{actual!r}")

        self.assertEqual(actual, expected)


class PackageOPFTestCase(TestCase):
    def test_generate(self):
        pkg = EpubPackage(
            options={},
            metadata={
                "novel_url": ":URL:",
                "site_id": ":SITE_ID:",
                "novel_id": ":NOVEL_ID:",
                "title": ":TITLE:",
            },
        )
        img = Image(
            url="https://example.com/imgs/novel-cover.jpg", mimetype="image/jpg", did_load=True, data=b":IMGDATA:"
        )
        pkg.add_image(img, content=img.data, is_cover_image=True)
        pkg.add_chapter(Chapter(url="http://example.come/chapter-2", chapter_no=2, title="Chapter 2. Example 2"))
        pkg.add_chapter(Chapter(url="http://example.come/chapter-1", chapter_no=1, title="Chapter 1. Example 1"))

        actual = pkg.opf.generate(pkg)
        expected = (
            f'<?xml version="1.0" encoding="utf-8"?>'
            f'<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="pywebnovel-uid">'
            # --- Metadata ---
            f'<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">'
            f'<dc:identifier id="pywebnovel-uid">{pkg.epub_uid}</dc:identifier>'
            f'<dc:title id="id-000">{pkg.metadata.title}</dc:title>'
            f'<dc:contributor id="id-001">PyWebnovel [https://github.com/bsandrow/PyWebnovel]</dc:contributor>'
            f"<dc:language>en</dc:language>"
            f"<dc:identifier>URL:{pkg.metadata.novel_url}</dc:identifier>"
            f"<dc:source>{pkg.metadata.novel_url}</dc:source>"
            f'<meta name="cover" content="{pkg.cover_image.file_id}"/>'
            f'<meta property="title-type" refines="#id-000">main</meta>'
            f'<meta property="role" refines="#id-000" scheme="marc:relators">bkp</meta>'
            f"</metadata>"
            # --- Manifest ---
            f"<manifest>"
            f'<item id="{pkg.cover_page.file_id}" href="{pkg.cover_page.relative_to(pkg.opf.parent)}" media-type="{pkg.cover_page.mimetype}"/>'
            f'<item id="{pkg.title_page.file_id}" href="{pkg.title_page.relative_to(pkg.opf.parent)}" media-type="{pkg.title_page.mimetype}"/>'
            f'<item id="{pkg.toc_page.file_id}" href="{pkg.toc_page.relative_to(pkg.opf.parent)}" media-type="{pkg.toc_page.mimetype}"/>'
            f'<item id="{pkg.chapter_files[0].file_id}" href="{pkg.chapter_files[0].relative_to(pkg.opf.parent)}" media-type="{pkg.chapter_files[0].mimetype}"/>'
            f'<item id="{pkg.chapter_files[1].file_id}" href="{pkg.chapter_files[1].relative_to(pkg.opf.parent)}" media-type="{pkg.chapter_files[1].mimetype}"/>'
            f'<item id="{pkg.ncx.file_id}" href="{pkg.ncx.relative_to(pkg.opf.parent)}" media-type="{pkg.ncx.mimetype}"/>'
            f'<item id="{pkg.stylesheet.file_id}" href="{pkg.stylesheet.relative_to(pkg.opf.parent)}" media-type="{pkg.stylesheet.mimetype}"/>'
            f'<item id="{pkg.nav.file_id}" href="{pkg.nav.relative_to(pkg.opf.parent)}" media-type="{pkg.nav.mimetype}"/>'
            f'<item id="{pkg.cover_image.file_id}" href="{pkg.cover_image.relative_to(pkg.opf.parent)}" media-type="{pkg.cover_image.mimetype}"/>'
            f"</manifest>"
            # --- Spine ---
            f'<spine toc="ncx">'
            f'<itemref idref="{pkg.cover_page.file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.title_page.file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.toc_page.file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.chapter_files[0].file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.chapter_files[1].file_id}" linear="yes"/>'
            f"</spine>"
            # --- Guide ---
            f"<guide>"
            f'<reference type="toc" title="Table of Contents" href="{pkg.toc_page.relative_to(pkg.opf.parent)}"/>'
            f'<reference type="cover" title="Cover" href="{pkg.cover_page.relative_to(pkg.opf.parent)}"/>'
            f'<reference type="start" title="Begin Reading" href="{pkg.cover_page.relative_to(pkg.opf.parent)}"/>'
            f"</guide>"
            f"</package>"
        ).encode("utf-8")

        self.assertEqual(actual, expected)

    def test_generate_with_author(self):
        pkg = EpubPackage(
            options={},
            metadata={
                "novel_url": ":URL:",
                "site_id": ":SITE_ID:",
                "novel_id": ":NOVEL_ID:",
                "title": ":TITLE:",
                "author": {"name": ":AUTHORNAME:"},
            },
        )
        img = Image(
            url="https://example.com/imgs/novel-cover.jpg", mimetype="image/jpg", did_load=True, data=b":IMGDATA:"
        )
        pkg.add_image(img, content=img.data, is_cover_image=True)
        pkg.add_chapter(Chapter(url="http://example.come/chapter-2", chapter_no=2, title="Chapter 2. Example 2"))
        pkg.add_chapter(Chapter(url="http://example.come/chapter-1", chapter_no=1, title="Chapter 1. Example 1"))

        actual = pkg.opf.generate(pkg)
        expected = (
            f'<?xml version="1.0" encoding="utf-8"?>'
            f'<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="pywebnovel-uid">'
            # --- Metadata ---
            f'<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">'
            f'<dc:identifier id="pywebnovel-uid">{pkg.epub_uid}</dc:identifier>'
            f'<dc:title id="id-000">{pkg.metadata.title}</dc:title>'
            f'<dc:creator id="id-001">{pkg.metadata.author.name}</dc:creator>'
            f'<dc:contributor id="id-002">PyWebnovel [https://github.com/bsandrow/PyWebnovel]</dc:contributor>'
            f"<dc:language>en</dc:language>"
            f"<dc:identifier>URL:{pkg.metadata.novel_url}</dc:identifier>"
            f"<dc:source>{pkg.metadata.novel_url}</dc:source>"
            f'<meta name="cover" content="{pkg.cover_image.file_id}"/>'
            f'<meta property="title-type" refines="#id-000">main</meta>'
            f'<meta property="role" refines="#id-001" scheme="marc:relators">aut</meta>'
            f'<meta property="role" refines="#id-001" scheme="marc:relators">bkp</meta>'
            f"</metadata>"
            # --- Manifest ---
            f"<manifest>"
            f'<item id="{pkg.cover_page.file_id}" href="{pkg.cover_page.relative_to(pkg.opf.parent)}" media-type="{pkg.cover_page.mimetype}"/>'
            f'<item id="{pkg.title_page.file_id}" href="{pkg.title_page.relative_to(pkg.opf.parent)}" media-type="{pkg.title_page.mimetype}"/>'
            f'<item id="{pkg.toc_page.file_id}" href="{pkg.toc_page.relative_to(pkg.opf.parent)}" media-type="{pkg.toc_page.mimetype}"/>'
            f'<item id="{pkg.chapter_files[0].file_id}" href="{pkg.chapter_files[0].relative_to(pkg.opf.parent)}" media-type="{pkg.chapter_files[0].mimetype}"/>'
            f'<item id="{pkg.chapter_files[1].file_id}" href="{pkg.chapter_files[1].relative_to(pkg.opf.parent)}" media-type="{pkg.chapter_files[1].mimetype}"/>'
            f'<item id="{pkg.ncx.file_id}" href="{pkg.ncx.relative_to(pkg.opf.parent)}" media-type="{pkg.ncx.mimetype}"/>'
            f'<item id="{pkg.stylesheet.file_id}" href="{pkg.stylesheet.relative_to(pkg.opf.parent)}" media-type="{pkg.stylesheet.mimetype}"/>'
            f'<item id="{pkg.nav.file_id}" href="{pkg.nav.relative_to(pkg.opf.parent)}" media-type="{pkg.nav.mimetype}"/>'
            f'<item id="{pkg.cover_image.file_id}" href="{pkg.cover_image.relative_to(pkg.opf.parent)}" media-type="{pkg.cover_image.mimetype}"/>'
            f"</manifest>"
            # --- Spine ---
            f'<spine toc="ncx">'
            f'<itemref idref="{pkg.cover_page.file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.title_page.file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.toc_page.file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.chapter_files[0].file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.chapter_files[1].file_id}" linear="yes"/>'
            f"</spine>"
            # --- Guide ---
            f"<guide>"
            f'<reference type="toc" title="Table of Contents" href="{pkg.toc_page.relative_to(pkg.opf.parent)}"/>'
            f'<reference type="cover" title="Cover" href="{pkg.cover_page.relative_to(pkg.opf.parent)}"/>'
            f'<reference type="start" title="Begin Reading" href="{pkg.cover_page.relative_to(pkg.opf.parent)}"/>'
            f"</guide>"
            f"</package>"
        ).encode("utf-8")

        self.assertEqual(actual, expected)

    def test_generate_without_images(self):
        pkg = EpubPackage(
            options={"include_images": False},
            metadata={
                "novel_url": ":URL:",
                "site_id": ":SITE_ID:",
                "novel_id": ":NOVEL_ID:",
                "title": ":TITLE:",
            },
        )
        img = Image(
            url="https://example.com/imgs/novel-cover.jpg", mimetype="image/jpg", did_load=True, data=b":IMGDATA:"
        )
        pkg.add_image(img, content=img.data, is_cover_image=True)
        pkg.add_chapter(Chapter(url="http://example.come/chapter-2", chapter_no=2, title="Chapter 2. Example 2"))
        pkg.add_chapter(Chapter(url="http://example.come/chapter-1", chapter_no=1, title="Chapter 1. Example 1"))

        actual = pkg.opf.generate(pkg)
        expected = (
            f'<?xml version="1.0" encoding="utf-8"?>'
            f'<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="pywebnovel-uid">'
            # --- Metadata ---
            f'<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">'
            f'<dc:identifier id="pywebnovel-uid">{pkg.epub_uid}</dc:identifier>'
            f'<dc:title id="id-000">{pkg.metadata.title}</dc:title>'
            f'<dc:contributor id="id-001">PyWebnovel [https://github.com/bsandrow/PyWebnovel]</dc:contributor>'
            f"<dc:language>en</dc:language>"
            f"<dc:identifier>URL:{pkg.metadata.novel_url}</dc:identifier>"
            f"<dc:source>{pkg.metadata.novel_url}</dc:source>"
            f'<meta property="title-type" refines="#id-000">main</meta>'
            f'<meta property="role" refines="#id-000" scheme="marc:relators">bkp</meta>'
            f"</metadata>"
            # --- Manifest ---
            f"<manifest>"
            f'<item id="{pkg.title_page.file_id}" href="{pkg.title_page.relative_to(pkg.opf.parent)}" media-type="{pkg.title_page.mimetype}"/>'
            f'<item id="{pkg.toc_page.file_id}" href="{pkg.toc_page.relative_to(pkg.opf.parent)}" media-type="{pkg.toc_page.mimetype}"/>'
            f'<item id="{pkg.chapter_files[0].file_id}" href="{pkg.chapter_files[0].relative_to(pkg.opf.parent)}" media-type="{pkg.chapter_files[0].mimetype}"/>'
            f'<item id="{pkg.chapter_files[1].file_id}" href="{pkg.chapter_files[1].relative_to(pkg.opf.parent)}" media-type="{pkg.chapter_files[1].mimetype}"/>'
            f'<item id="{pkg.ncx.file_id}" href="{pkg.ncx.relative_to(pkg.opf.parent)}" media-type="{pkg.ncx.mimetype}"/>'
            f'<item id="{pkg.stylesheet.file_id}" href="{pkg.stylesheet.relative_to(pkg.opf.parent)}" media-type="{pkg.stylesheet.mimetype}"/>'
            f'<item id="{pkg.nav.file_id}" href="{pkg.nav.relative_to(pkg.opf.parent)}" media-type="{pkg.nav.mimetype}"/>'
            f"</manifest>"
            # --- Spine ---
            f'<spine toc="ncx">'
            f'<itemref idref="{pkg.title_page.file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.toc_page.file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.chapter_files[0].file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.chapter_files[1].file_id}" linear="yes"/>'
            f"</spine>"
            # --- Guide ---
            f"<guide>"
            f'<reference type="toc" title="Table of Contents" href="{pkg.toc_page.relative_to(pkg.opf.parent)}"/>'
            f'<reference type="start" title="Begin Reading" href="{pkg.title_page.relative_to(pkg.opf.parent)}"/>'
            f"</guide>"
            f"</package>"
        ).encode("utf-8")

        self.assertEqual(actual, expected)

    def test_generate_with_genres(self):
        pkg = EpubPackage(
            options={},
            metadata={
                "novel_url": ":URL:",
                "site_id": ":SITE_ID:",
                "novel_id": ":NOVEL_ID:",
                "title": ":TITLE:",
                "genres": ["Comedy", "Tragedy", "Drama"],
            },
        )
        img = Image(
            url="https://example.com/imgs/novel-cover.jpg", mimetype="image/jpg", did_load=True, data=b":IMGDATA:"
        )
        pkg.add_image(img, content=img.data, is_cover_image=True)
        pkg.add_chapter(Chapter(url="http://example.come/chapter-2", chapter_no=2, title="Chapter 2. Example 2"))
        pkg.add_chapter(Chapter(url="http://example.come/chapter-1", chapter_no=1, title="Chapter 1. Example 1"))

        actual = pkg.opf.generate(pkg)
        expected = (
            f'<?xml version="1.0" encoding="utf-8"?>'
            f'<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="pywebnovel-uid">'
            # --- Metadata ---
            f'<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">'
            f'<dc:identifier id="pywebnovel-uid">{pkg.epub_uid}</dc:identifier>'
            f'<dc:title id="id-000">{pkg.metadata.title}</dc:title>'
            f'<dc:contributor id="id-001">PyWebnovel [https://github.com/bsandrow/PyWebnovel]</dc:contributor>'
            f"<dc:language>en</dc:language>"
            f"<dc:subject>{pkg.metadata.genres[0]}</dc:subject>"
            f"<dc:subject>{pkg.metadata.genres[1]}</dc:subject>"
            f"<dc:subject>{pkg.metadata.genres[2]}</dc:subject>"
            f"<dc:identifier>URL:{pkg.metadata.novel_url}</dc:identifier>"
            f"<dc:source>{pkg.metadata.novel_url}</dc:source>"
            f'<meta name="cover" content="{pkg.cover_image.file_id}"/>'
            f'<meta property="title-type" refines="#id-000">main</meta>'
            f'<meta property="role" refines="#id-000" scheme="marc:relators">bkp</meta>'
            f"</metadata>"
            # --- Manifest ---
            f"<manifest>"
            f'<item id="{pkg.cover_page.file_id}" href="{pkg.cover_page.relative_to(pkg.opf.parent)}" media-type="{pkg.cover_page.mimetype}"/>'
            f'<item id="{pkg.title_page.file_id}" href="{pkg.title_page.relative_to(pkg.opf.parent)}" media-type="{pkg.title_page.mimetype}"/>'
            f'<item id="{pkg.toc_page.file_id}" href="{pkg.toc_page.relative_to(pkg.opf.parent)}" media-type="{pkg.toc_page.mimetype}"/>'
            f'<item id="{pkg.chapter_files[0].file_id}" href="{pkg.chapter_files[0].relative_to(pkg.opf.parent)}" media-type="{pkg.chapter_files[0].mimetype}"/>'
            f'<item id="{pkg.chapter_files[1].file_id}" href="{pkg.chapter_files[1].relative_to(pkg.opf.parent)}" media-type="{pkg.chapter_files[1].mimetype}"/>'
            f'<item id="{pkg.ncx.file_id}" href="{pkg.ncx.relative_to(pkg.opf.parent)}" media-type="{pkg.ncx.mimetype}"/>'
            f'<item id="{pkg.stylesheet.file_id}" href="{pkg.stylesheet.relative_to(pkg.opf.parent)}" media-type="{pkg.stylesheet.mimetype}"/>'
            f'<item id="{pkg.nav.file_id}" href="{pkg.nav.relative_to(pkg.opf.parent)}" media-type="{pkg.nav.mimetype}"/>'
            f'<item id="{pkg.cover_image.file_id}" href="{pkg.cover_image.relative_to(pkg.opf.parent)}" media-type="{pkg.cover_image.mimetype}"/>'
            f"</manifest>"
            # --- Spine ---
            f'<spine toc="ncx">'
            f'<itemref idref="{pkg.cover_page.file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.title_page.file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.toc_page.file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.chapter_files[0].file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.chapter_files[1].file_id}" linear="yes"/>'
            f"</spine>"
            # --- Guide ---
            f"<guide>"
            f'<reference type="toc" title="Table of Contents" href="{pkg.toc_page.relative_to(pkg.opf.parent)}"/>'
            f'<reference type="cover" title="Cover" href="{pkg.cover_page.relative_to(pkg.opf.parent)}"/>'
            f'<reference type="start" title="Begin Reading" href="{pkg.cover_page.relative_to(pkg.opf.parent)}"/>'
            f"</guide>"
            f"</package>"
        ).encode("utf-8")

        self.assertEqual(actual, expected)

    def test_generate_with_text_summary(self):
        pkg = EpubPackage(
            options={},
            metadata={
                "novel_url": ":URL:",
                "site_id": ":SITE_ID:",
                "novel_id": ":NOVEL_ID:",
                "title": ":TITLE:",
                "summary": "This\nIs\nText",
                "summary_type": "text",
            },
        )
        img = Image(
            url="https://example.com/imgs/novel-cover.jpg", mimetype="image/jpg", did_load=True, data=b":IMGDATA:"
        )
        pkg.add_image(img, content=img.data, is_cover_image=True)
        pkg.add_chapter(Chapter(url="http://example.come/chapter-2", chapter_no=2, title="Chapter 2. Example 2"))
        pkg.add_chapter(Chapter(url="http://example.come/chapter-1", chapter_no=1, title="Chapter 1. Example 1"))

        actual = pkg.opf.generate(pkg)
        expected = (
            f'<?xml version="1.0" encoding="utf-8"?>'
            f'<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="pywebnovel-uid">'
            # --- Metadata ---
            f'<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">'
            f'<dc:identifier id="pywebnovel-uid">{pkg.epub_uid}</dc:identifier>'
            f'<dc:title id="id-000">{pkg.metadata.title}</dc:title>'
            f'<dc:contributor id="id-001">PyWebnovel [https://github.com/bsandrow/PyWebnovel]</dc:contributor>'
            f"<dc:language>en</dc:language>"
            f"<dc:description>{pkg.metadata.summary}</dc:description>"
            f"<dc:identifier>URL:{pkg.metadata.novel_url}</dc:identifier>"
            f"<dc:source>{pkg.metadata.novel_url}</dc:source>"
            f'<meta name="cover" content="{pkg.cover_image.file_id}"/>'
            f'<meta property="title-type" refines="#id-000">main</meta>'
            f'<meta property="role" refines="#id-000" scheme="marc:relators">bkp</meta>'
            f"</metadata>"
            # --- Manifest ---
            f"<manifest>"
            f'<item id="{pkg.cover_page.file_id}" href="{pkg.cover_page.relative_to(pkg.opf.parent)}" media-type="{pkg.cover_page.mimetype}"/>'
            f'<item id="{pkg.title_page.file_id}" href="{pkg.title_page.relative_to(pkg.opf.parent)}" media-type="{pkg.title_page.mimetype}"/>'
            f'<item id="{pkg.toc_page.file_id}" href="{pkg.toc_page.relative_to(pkg.opf.parent)}" media-type="{pkg.toc_page.mimetype}"/>'
            f'<item id="{pkg.chapter_files[0].file_id}" href="{pkg.chapter_files[0].relative_to(pkg.opf.parent)}" media-type="{pkg.chapter_files[0].mimetype}"/>'
            f'<item id="{pkg.chapter_files[1].file_id}" href="{pkg.chapter_files[1].relative_to(pkg.opf.parent)}" media-type="{pkg.chapter_files[1].mimetype}"/>'
            f'<item id="{pkg.ncx.file_id}" href="{pkg.ncx.relative_to(pkg.opf.parent)}" media-type="{pkg.ncx.mimetype}"/>'
            f'<item id="{pkg.stylesheet.file_id}" href="{pkg.stylesheet.relative_to(pkg.opf.parent)}" media-type="{pkg.stylesheet.mimetype}"/>'
            f'<item id="{pkg.nav.file_id}" href="{pkg.nav.relative_to(pkg.opf.parent)}" media-type="{pkg.nav.mimetype}"/>'
            f'<item id="{pkg.cover_image.file_id}" href="{pkg.cover_image.relative_to(pkg.opf.parent)}" media-type="{pkg.cover_image.mimetype}"/>'
            f"</manifest>"
            # --- Spine ---
            f'<spine toc="ncx">'
            f'<itemref idref="{pkg.cover_page.file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.title_page.file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.toc_page.file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.chapter_files[0].file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.chapter_files[1].file_id}" linear="yes"/>'
            f"</spine>"
            # --- Guide ---
            f"<guide>"
            f'<reference type="toc" title="Table of Contents" href="{pkg.toc_page.relative_to(pkg.opf.parent)}"/>'
            f'<reference type="cover" title="Cover" href="{pkg.cover_page.relative_to(pkg.opf.parent)}"/>'
            f'<reference type="start" title="Begin Reading" href="{pkg.cover_page.relative_to(pkg.opf.parent)}"/>'
            f"</guide>"
            f"</package>"
        ).encode("utf-8")

        self.assertEqual(actual, expected)

    def test_generate_with_html_summary(self):
        pkg = EpubPackage(
            options={},
            metadata={
                "novel_url": ":URL:",
                "site_id": ":SITE_ID:",
                "novel_id": ":NOVEL_ID:",
                "title": ":TITLE:",
                "summary": "<div><p>This\nIs\nText</p></div>",
                "summary_type": "html",
            },
        )
        img = Image(
            url="https://example.com/imgs/novel-cover.jpg", mimetype="image/jpg", did_load=True, data=b":IMGDATA:"
        )
        pkg.add_image(img, content=img.data, is_cover_image=True)
        pkg.add_chapter(Chapter(url="http://example.come/chapter-2", chapter_no=2, title="Chapter 2. Example 2"))
        pkg.add_chapter(Chapter(url="http://example.come/chapter-1", chapter_no=1, title="Chapter 1. Example 1"))

        actual = pkg.opf.generate(pkg)
        expected = (
            f'<?xml version="1.0" encoding="utf-8"?>'
            f'<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="pywebnovel-uid">'
            # --- Metadata ---
            f'<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">'
            f'<dc:identifier id="pywebnovel-uid">{pkg.epub_uid}</dc:identifier>'
            f'<dc:title id="id-000">{pkg.metadata.title}</dc:title>'
            f'<dc:contributor id="id-001">PyWebnovel [https://github.com/bsandrow/PyWebnovel]</dc:contributor>'
            f"<dc:language>en</dc:language>"
            f"<dc:description>{BeautifulSoup(pkg.metadata.summary, 'html.parser').text}</dc:description>"
            f"<dc:identifier>URL:{pkg.metadata.novel_url}</dc:identifier>"
            f"<dc:source>{pkg.metadata.novel_url}</dc:source>"
            f'<meta name="cover" content="{pkg.cover_image.file_id}"/>'
            f'<meta property="title-type" refines="#id-000">main</meta>'
            f'<meta property="role" refines="#id-000" scheme="marc:relators">bkp</meta>'
            f"</metadata>"
            # --- Manifest ---
            f"<manifest>"
            f'<item id="{pkg.cover_page.file_id}" href="{pkg.cover_page.relative_to(pkg.opf.parent)}" media-type="{pkg.cover_page.mimetype}"/>'
            f'<item id="{pkg.title_page.file_id}" href="{pkg.title_page.relative_to(pkg.opf.parent)}" media-type="{pkg.title_page.mimetype}"/>'
            f'<item id="{pkg.toc_page.file_id}" href="{pkg.toc_page.relative_to(pkg.opf.parent)}" media-type="{pkg.toc_page.mimetype}"/>'
            f'<item id="{pkg.chapter_files[0].file_id}" href="{pkg.chapter_files[0].relative_to(pkg.opf.parent)}" media-type="{pkg.chapter_files[0].mimetype}"/>'
            f'<item id="{pkg.chapter_files[1].file_id}" href="{pkg.chapter_files[1].relative_to(pkg.opf.parent)}" media-type="{pkg.chapter_files[1].mimetype}"/>'
            f'<item id="{pkg.ncx.file_id}" href="{pkg.ncx.relative_to(pkg.opf.parent)}" media-type="{pkg.ncx.mimetype}"/>'
            f'<item id="{pkg.stylesheet.file_id}" href="{pkg.stylesheet.relative_to(pkg.opf.parent)}" media-type="{pkg.stylesheet.mimetype}"/>'
            f'<item id="{pkg.nav.file_id}" href="{pkg.nav.relative_to(pkg.opf.parent)}" media-type="{pkg.nav.mimetype}"/>'
            f'<item id="{pkg.cover_image.file_id}" href="{pkg.cover_image.relative_to(pkg.opf.parent)}" media-type="{pkg.cover_image.mimetype}"/>'
            f"</manifest>"
            # --- Spine ---
            f'<spine toc="ncx">'
            f'<itemref idref="{pkg.cover_page.file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.title_page.file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.toc_page.file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.chapter_files[0].file_id}" linear="yes"/>'
            f'<itemref idref="{pkg.chapter_files[1].file_id}" linear="yes"/>'
            f"</spine>"
            # --- Guide ---
            f"<guide>"
            f'<reference type="toc" title="Table of Contents" href="{pkg.toc_page.relative_to(pkg.opf.parent)}"/>'
            f'<reference type="cover" title="Cover" href="{pkg.cover_page.relative_to(pkg.opf.parent)}"/>'
            f'<reference type="start" title="Begin Reading" href="{pkg.cover_page.relative_to(pkg.opf.parent)}"/>'
            f"</guide>"
            f"</package>"
        ).encode("utf-8")

        self.assertEqual(actual, expected)
