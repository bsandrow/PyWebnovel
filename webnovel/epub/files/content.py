from typing import TYPE_CHECKING

from xml.dom.minidom import getDOMImplementation

from webnovel.epub.files import EpubFileInterface
from webnovel.epub.files.jinja import JINJA
from webnovel.xml import create_element, set_element_attributes

if TYPE_CHECKING:
    from webnovel.epub.pkg import EpubPackage


class Stylesheet(EpubFileInterface):
    """"""

    file_id: str = "style"
    filename: str = "OEBPS/stylesheet.css"
    mimetype: str = "text/css"
    pkg: "EpubPackage"

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg


class TitlePage(EpubFileInterface):
    """The title page of the epub."""

    file_id: str = "title_page"
    filename: str = "OEBPS/title_page.xhtml"
    mimetype: str = "application/xhtml+xml"
    title: str = "Title Page"
    include_in_spine: bool = True
    data: bytes = None
    title_page_css: str = "pywebnovel-titlepage"
    pkg: "EpubPackage"

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg

    def generate(self):
        template = JINJA.get_template("title_page.xhtml")
        self.data = template.render(
            novel=self.pkg.novel,
            stylesheet=self.pkg.stylesheet_path,
            title_page_css=self.title_page_css
        ).encode("utf-8")


class CoverPage(EpubFileInterface):
    """The cover page (containing the cover image) of the epub."""

    file_id: str = "cover"
    filename: str = "OEBPS/cover.xhtml"
    mimetype: str = "application/xhtml+xml"
    title: str = None
    include_in_spine: bool = True
    data: bytes = None

    def generate(self, **template_kwargs):
        template = JINJA.get_template("cover.xhtml")
        self.data = template.render(**template_kwargs).encode("utf-8")


class NavigationControlFile(EpubFileInterface):
    """
    The toc.ncx file or 'Navigation Control for XML' file.

    The NCX file abbreviated as a Navigation Control file for XML, usually named toc.ncx. This file consists of the
    hierarchical table of contents for an EPUB file. The specification for NCX was developed for Digital Talking Book
    (DTB) and this file format is maintained by the DAISY Consortium and is not a part of the EPUB specification. The
    NCX file includes a mime-type of application/x-dtbncx+xml into it.

    Source: https://docs.fileformat.com/ebook/ncx/
    """

    file_id: str = "ncx"
    filename: str = "toc.ncx"
    mimetype: str = "application/x-dtbncx+xml"
    title: str = None
    include_in_spine: bool = False
    data: bytes = None
    pkg: "EpubPackage" = None

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg

    def generate(self):
        dom = getDOMImplementation().createDocument(None, "ncx", None)
        set_element_attributes(
            dom.documentElement,
            {
                "version": "2005-1",
                "xmlns": "http://www.daisy.org/z3986/2005/ncx/",
            }
        )
        head = create_element(dom, "head", parent=dom.documentElement)
        doc_title = create_element(dom, "docTitle", parent=dom.documentElement)
        navmap = create_element(dom, "navMap", parent=dom.documentElement)

        create_element(dom, "meta", parent=head, attributes={"name": "dtb:uid", "content": self.pkg.epub_uid})
        create_element(dom, "meta", parent=head, attributes={"name": "dtb:depth", "content": "1"})
        create_element(dom, "meta", parent=head, attributes={"name": "dtb:totalPageCount", "content": "0"})
        create_element(dom, "meta", parent=head, attributes={"name": "dtb:maxPageNumber", "content": "0"})
        create_element(dom, "text", parent=doc_title, text=self.pkg.novel.title)

        for index, epub_file in enumerate(self.pkg.files):
            # Skip: cover.xhtml, toc.ncx, stylesheet.css (and images)
            if epub_file.file_id in ("cover", "ncx", "style"):
                continue

            nav_point = create_element(
                dom, "navPoint", parent=navmap, attributes={"id": epub_file.file_id, "playOrder": index}
            )
            nav_label = create_element(dom, "navLabel", parent=nav_point)
            create_element(dom, "text", parent=nav_label, text=epub_file)
            create_element(dom, "content", parent=nav_point, attributes={"src": epub_file.filename})

        self.data = dom.toxml(encoding="utf-8")


class TableOfContentsPage(EpubFileInterface):
    """The page containing the Table of Contents for the epub."""

    file_id: str = "toc_page"
    filename: str = "OEBPS/toc_page.xhtml"
    mimetype: str = "application/xhtml+xml"
    title: str = "Table of Contents"
    include_in_spine: bool = True
    data: bytes = None
    pkg: "EpubPackage" = None

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg

    def generate(self):
        pass


class NavXhtml(EpubFileInterface):
    """Class for the nav.xhtml file."""
    file_id: str = "nav"
    filename: str = "nav.xhtml"
    mimetype: str = "application/xhtml+xml"
    title: str = None
    include_in_spine: bool = False
    data: bytes = None
    pkg: "EpubPackage" = None

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg

    def generate(self):
        pass
