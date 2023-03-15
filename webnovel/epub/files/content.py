"""File."""

from typing import TYPE_CHECKING
from xml.dom.minidom import getDOMImplementation

from webnovel.epub.files import EpubFileInterface
from webnovel.epub.files.jinja import JINJA
from webnovel.xml import create_element, set_element_attributes

if TYPE_CHECKING:
    from webnovel.epub.pkg import EpubPackage


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
        """Generate."""
        template = JINJA.get_template("title_page.xhtml")
        self.data = template.render(
            novel=self.pkg.novel, stylesheet=self.pkg.stylesheet_path, title_page_css=self.title_page_css
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
        """Generate."""
        template = JINJA.get_template("cover.xhtml")
        self.data = template.render(**template_kwargs).encode("utf-8")


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
        """Generate."""


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
        """Generate."""
