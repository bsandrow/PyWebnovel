"""File."""

from typing import TYPE_CHECKING
from xml.dom.minidom import getDOMImplementation

from webnovel.epub.files import EpubFileInterface
from webnovel.xml import create_element, set_element_attributes

if TYPE_CHECKING:
    from webnovel.epub.pkg import EpubPackage


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
