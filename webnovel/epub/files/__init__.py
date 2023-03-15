"""Classes to represent and generate the files that will be in the epub package."""

import json
import pkgutil
from typing import TYPE_CHECKING
from xml.dom.minidom import getDOMImplementation

from jinja2 import Environment, PackageLoader, select_autoescape

from webnovel.xml import create_element, set_element_attributes

from .base import BasicFileInterface, EpubFile, EpubFileInterface
from .content import CoverPage, TableOfContentsPage, TitlePage
from .images import EpubImage, EpubImages

if TYPE_CHECKING:
    from webnovel.epub.pkg import EpubPackage


JINJA = Environment(loader=PackageLoader("webnovel.epub"), autoescape=select_autoescape())


class PyWebNovelJSON(EpubFileInterface):
    """
    A JSON file storing information about the webnovel.

    This file is a place to store PyWebnovel specific information so that it can
    be read out of existing epub files to do things like (e.g.) fetch additional
    chapters and add them to the file.

    This file is not part of the spec, and is app-specific (to PyWebnovel).
    """

    file_id: str = "pywebnovel-meta"
    filename: str = "pywebnovel.json"
    mimetype: str = "application/json"
    title: str = None
    include_in_spine: bool = False
    data: bytes = None
    pkg: "EpubPackage" = None

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg

    def generate(self) -> None:
        """Serialize the novel information into the data attribute as JSON."""
        data = {}
        self.data = json.dumps(data).encode("utf-8")


class MimetypeFile(BasicFileInterface):
    """
    A simple file containing the mimetype of the epub package.

    It's part of the spec to have a file called 'mimetype' with a just the
    mimetype as the contents.
    """

    file_id: str = "mimetype"
    filename: str = "mimetype"
    data: bytes = b"application/epub+zip"
    pkg: "EpubPackage"

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg


class ContainerXML(BasicFileInterface):
    """
    A Top-Level XML File in the Epub Format.

    This file basically only exists to specify the name and location of the
    package.opf file.  Technically that file doesn't need to be named
    package.opf and could be anywhere in the file structure, so long as this
    file points to it correctly.
    """

    file_id: str = "container-xml"
    filename: str = "META-INF/container.xml"
    data: bytes = None
    pkg: "EpubPackage" = None

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg

    def generate(self) -> None:
        """Generate the contents of this XML file into data attribute."""
        dom = getDOMImplementation().createDocument(None, "container", None)
        dom.documentElement.setAttribute("version", "1.0")
        dom.documentElement.setAttribute("xmlns", "urn:oasis:names:tc:opendocument:xmlns:container")
        root_files = dom.createElement("rootfiles")
        dom.documentElement.appendChild(root_files)
        root_file = dom.createElement("rootfile")
        root_file.setAttribute("full-path", self.pkg.pkg_opf_path)
        root_file.setAttribute("media-type", "application/oebps-package+xml")
        root_files.appendChild(root_file)
        self.data = dom.toxml(encoding="utf-8")


class Stylesheet(EpubFileInterface):
    """The stylesheet for the ereader to use in rendering."""

    file_id: str = "style"
    filename: str = "OEBPS/stylesheet.css"
    mimetype: str = "text/css"
    pkg: "EpubPackage"

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg

    def generate(self) -> None:
        """Load the stylesheet data from embeded stylesheet."""
        self.data = pkgutil.get_data("webnovel.epub", "content/stylesheet.css")


class NavigationControlFile(EpubFileInterface):
    """
    The toc.ncx file or 'Navigation Control for XML' file.

    The NCX file abbreviated as a Navigation Control file for XML, usually named
    toc.ncx. This file consists of the hierarchical table of contents for an
    EPUB file. The specification for NCX was developed for Digital Talking Book
    (DTB) and this file format is maintained by the DAISY Consortium and is not
    a part of the EPUB specification. The NCX file includes a mime-type of
    application/x-dtbncx+xml into it.

    Source: https://docs.fileformat.com/ebook/ncx/
    """

    file_id: str = "ncx"
    filename: str = "toc.ncx"
    mimetype: str = "application/x-dtbncx+xml"
    title: str = None
    include_in_spine: bool = False
    data: bytes = None
    pkg: "EpubPackage" = None

    # Skip: cover.xhtml, toc.ncx, stylesheet.css (and images)
    files_to_ignore = ("cover", "ncx", "style", "mimetype", "container-xml", "pywebnovel-meta")

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg

    def generate(self):
        """Generate XML Contents into data attribute."""
        dom = getDOMImplementation().createDocument(None, "ncx", None)
        set_element_attributes(
            dom.documentElement,
            {
                "version": "2005-1",
                "xmlns": "http://www.daisy.org/z3986/2005/ncx/",
            },
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
            # TODO: There's probably a better way to just label the files that
            #       need to be included here rather than maintaining a
            #       blacklist.  A property off the file class or a whitelist of
            #       classes, etc.
            if epub_file.file_id in self.files_to_ignore:
                continue
            nav_point = create_element(
                dom, "navPoint", parent=navmap, attributes={"id": epub_file.file_id, "playOrder": index}
            )
            nav_label = create_element(dom, "navLabel", parent=nav_point)
            create_element(dom, "text", parent=nav_label, text=epub_file)
            create_element(dom, "content", parent=nav_point, attributes={"src": epub_file.filename})

        self.data = dom.toxml(encoding="utf-8")


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
        """Generate title page XHMTL file."""
        template = JINJA.get_template("title_page.xhtml")
        self.data = template.render(
            novel=self.pkg.novel, stylesheet=Stylesheet.filename, title_page_css=self.title_page_css
        ).encode("utf-8")
