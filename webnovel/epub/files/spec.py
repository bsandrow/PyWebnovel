from typing import TYPE_CHECKING

from xml.dom.minidom import getDOMImplementation

from webnovel.epub.files import BasicFileInterface

if TYPE_CHECKING:
    from webnovel.epub.pkg import EpubPackage


class MimetypeFile(BasicFileInterface):
    filename: str = "mimetype"
    data: bytes = b"application/epub+zip"
    pkg: "EpubPackage"

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg


class ContainerXML(BasicFileInterface):
    filename: str = "META-INF/container.xml"
    data: bytes = None
    pkg: "EpubPackage" = None

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg

    def generate(self) -> None:
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


