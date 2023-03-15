"""Classes to represent and generate the files that will be in the epub package."""

import json
import pkgutil
from typing import TYPE_CHECKING
from xml.dom.minidom import getDOMImplementation

from .base import BasicFileInterface, EpubFile, EpubFileInterface
from .content import CoverPage, NavigationControlFile, TableOfContentsPage, TitlePage
from .images import EpubImage, EpubImages

if TYPE_CHECKING:
    from webnovel.epub.pkg import EpubPackage


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
