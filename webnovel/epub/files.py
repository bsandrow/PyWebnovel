"""Classes to represent and generate the files that will be in the epub package."""

from dataclasses import dataclass
import json
import pkgutil
from typing import TYPE_CHECKING, Optional
from xml.dom.minidom import Document, Element, getDOMImplementation

from jinja2 import Environment, PackageLoader, select_autoescape

from webnovel.data import Chapter, Image
from webnovel.xml import create_element, set_element_attributes

if TYPE_CHECKING:
    from webnovel.epub.pkg import EpubPackage


JINJA = Environment(
    loader=PackageLoader("webnovel.epub", package_path="content/templates"), autoescape=select_autoescape()
)


class EpubFileInterface:
    """Interface use for files in the epub package."""

    file_id: str
    filename: str
    mimetype: str
    title: Optional[str] = None
    include_in_spine: bool = False
    include_in_manifest: bool = True
    data: Optional[bytes] = None
    pkg: Optional["EpubPackage"] = None


@dataclass
class EpubFile(EpubFileInterface):
    """Class representing a file in the epub package."""

    file_id: str
    filename: str
    mimetype: str
    pkg: Optional["EpubPackage"] = None
    title: Optional[str] = None
    include_in_spine: bool = False
    data: Optional[bytes] = None


class EpubImage(EpubFile):
    """Class representing an image in the epub package."""

    @classmethod
    def from_image(cls, image: Image, image_id: str) -> "EpubImage":
        """Create an EpubImage from an Image."""
        return EpubImage(
            file_id=image_id,
            filename=f"OEBPS/{image_id}{image.extension}",
            mimetype=image.mimetype,
            data=image.data,
        )


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
    include_in_manifest: bool = False
    data: bytes = None
    pkg: "EpubPackage" = None

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg

    def generate(self) -> None:
        """Serialize the novel information into the data attribute as JSON."""
        data = {}
        self.data = json.dumps(data).encode("utf-8")


class MimetypeFile(EpubFileInterface):
    """
    A simple file containing the mimetype of the epub package.

    It's part of the spec to have a file called 'mimetype' with a just the
    mimetype as the contents.
    """

    file_id: str = "mimetype"
    filename: str = "mimetype"
    data: bytes = b"application/epub+zip"
    include_in_manifest: bool = False
    pkg: "EpubPackage"

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg


class ContainerXML(EpubFileInterface):
    """
    A Top-Level XML File in the Epub Format.

    This file basically only exists to specify the name and location of the
    package.opf file.  Technically that file doesn't need to be named
    package.opf and could be anywhere in the file structure, so long as this
    file points to it correctly.
    """

    file_id: str = "container-xml"
    filename: str = "META-INF/container.xml"
    include_in_manifest: bool = False
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

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg

    def get_whitelisted_files(self):
        """Return a list of files from the package that user-facing and should be made into jump points."""
        return [epub_file for epub_file in self.pkg.files if isinstance(epub_file, (TitlePage,))]

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
        navmap_node = create_element(dom, "navMap", parent=dom.documentElement)

        create_element(dom, "meta", parent=head, attributes={"name": "dtb:uid", "content": self.pkg.epub_uid})
        create_element(dom, "meta", parent=head, attributes={"name": "dtb:depth", "content": "1"})
        create_element(dom, "meta", parent=head, attributes={"name": "dtb:totalPageCount", "content": "0"})
        create_element(dom, "meta", parent=head, attributes={"name": "dtb:maxPageNumber", "content": "0"})
        create_element(dom, "text", parent=doc_title, text=self.pkg.novel.title)

        for index, epub_file in enumerate(self.get_whitelisted_files()):
            nav_point_node = create_element(
                dom, "navPoint", parent=navmap_node, attributes={"id": epub_file.file_id, "playOrder": index}
            )
            nav_label = create_element(dom, "navLabel", parent=nav_point_node)
            create_element(dom, "text", parent=nav_label, text=epub_file.title)
            create_element(dom, "content", parent=nav_point_node, attributes={"src": epub_file.filename})

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


class CoverPage(EpubFileInterface):
    """The cover page (containing the cover image) of the epub."""

    file_id: str = "cover"
    filename: str = "OEBPS/cover.xhtml"
    mimetype: str = "application/xhtml+xml"
    title: str = None
    include_in_spine: bool = True
    data: bytes = None
    pkg: "EpubPackage"

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg

    def generate(self, **template_kwargs):
        """Generate cover page XHTML."""
        template_kwargs.setdefault("cover_image", self.pkg.cover_image)
        template = JINJA.get_template("cover.xhtml")
        self.data = template.render(**template_kwargs).encode("utf-8")


class PackageOPF(EpubFileInterface):
    """The Main XML file that acts as a manifest for the epub package."""

    file_id: str = "opf"
    filename: str = "package.opf"
    data: bytes = None
    include_in_manifest: bool = False

    def __init__(self, pkg: "EpubPackage", filename: str = None) -> None:
        self.filename = filename or self.filename
        self.pkg = pkg

    @staticmethod
    def generate_guide(dom: Document, pkg: "EpubPackage") -> Optional[Element]:
        """
        Generate <guide> element for PackageOPF file.

        Only generated if there is a cover image and include_images=True for the parent package.
        """
        if pkg.include_images and pkg.files.has_cover_page:
            guide = create_element(dom, "guide")
            attrs = {"type": "cover", "title": "Cover", "href": CoverPage.filename}
            create_element(dom, "reference", parent=guide, attributes=attrs)
            return guide
        return None

    @staticmethod
    def generate_spine(dom: Document, pkg: "EpubPackage") -> Element:
        """Generate a <spine> for the OPF package."""
        spine = create_element(dom, "spine", attributes={"toc": "ncx"})
        for epub_file in pkg.files:
            if epub_file.include_in_spine and epub_file.file_id is not None:
                create_element(dom, "itemref", attributes={"idref": epub_file.file_id, "linear": "yes"}, parent=spine)
        return spine

    @staticmethod
    def generate_manifest(dom: Document, pkg: "EpubPackage") -> Element:
        """Generate a <manifest> for the OPF package."""
        manifest = create_element(dom, "manifest")

        for epub_file in pkg.files:
            if epub_file.include_in_manifest:
                attrs = {"id": epub_file.file_id, "href": epub_file.filename, "media-type": epub_file.mimetype}
                create_element(dom, "item", attributes=attrs, parent=manifest)

        if pkg.is_epub3:
            attrs = {"href": "nav.xhtml", "id": "nav", "media-type": "application/xhtml+xml", "properties": "nav"}
            create_element(dom, "item", attributes=attrs, parent=manifest)

        return manifest

    @staticmethod
    def generate_metadata(dom: Document, pkg: "EpubPackage") -> Element:
        """Generate the <metadata> for the novel."""
        attrs = {"xmlns:dc": "http://purl.org/dc/elements/1.1/", "xmlns:opf": "http://www.idpf.org/2007/opf"}
        metadata = create_element(dom, "metadata", attributes=attrs)
        epub3_refs = Epub3Refs(dom)
        create_element(dom, "dc:identifier", text=pkg.epub_uid, attributes={"id": "pywebnovel-uid"}, parent=metadata)

        if pkg.novel.title:
            tag_id = epub3_refs.get_tag_id()
            create_element(dom, "dc:title", text=pkg.novel.title, attributes={"id": tag_id}, parent=metadata)
            epub3_refs.add_ref(ref_type="main", ref_property="title-type", tag_id=tag_id)

        if pkg.novel.author:
            # TODO support list of authors
            tag_id = epub3_refs.get_tag_id()
            if pkg.is_epub3:
                create_element(
                    dom, "dc:creator", text=pkg.novel.author.name, attributes={"id": tag_id}, parent=metadata
                )
            else:
                create_element(
                    dom, "dc:creator", text=pkg.novel.author.name, attributes={"opf:role": "aut"}, parent=metadata
                )
            epub3_refs.add_ref(ref_type="aut", tag_id=tag_id, ref_property="role")

        attrs = {"id": epub3_refs.get_tag_id()}
        text = "PyWebnovel [https://github.com/bsandrow/PyWebnovel]"
        create_element(dom, "dc:contributor", text=text, attributes=attrs, parent=metadata)
        epub3_refs.add_ref(ref_type="bkp", ref_property="role", tag_id=tag_id)

        # TODO add language_code to Novel
        langcode = "en"
        create_element(dom, "dc:language", text=langcode, parent=metadata)

        # TODO published / created / updated / calibre (add to Novel)

        if pkg.novel.summary:
            create_element(dom, "dc:description", text=pkg.novel.summary, parent=metadata)

        if pkg.novel.genres:
            for genre in pkg.novel.genres:
                create_element(dom, "dc:subject", text=genre, parent=metadata)

        # TODO site

        # Novel URL
        create_element(
            dom,
            "dc:identifier",
            text=f"URL:{pkg.novel.url}" if pkg.is_epub3 else pkg.novel.url,
            attributes=None if pkg.is_epub3 else {"opf:scheme": "URL"},
            parent=metadata,
        )
        create_element(dom, "dc:source", text=pkg.novel.url, parent=metadata)

        if pkg.include_images and pkg.files.has_cover_page:
            # <meta name="cover" content="$COVER_IMAGE_ID"/>
            # Note: Order matters here for some broken ereader implementations (i.e. "name" must come before
            #       "content")
            attrs = {"name": "cover", "content": pkg.cover_image.file_id}
            create_element(dom, "meta", parent=metadata, attributes=attrs)

        if pkg.is_epub3:
            for ref in epub3_refs.refs:
                metadata.appendChild(ref)

        return metadata

    def generate(self) -> None:
        """Generate package.opf file."""
        dom = getDOMImplementation().createDocument(None, "package", None)
        pkg_element = dom.documentElement
        set_element_attributes(
            pkg_element,
            {
                "version": "3.0" if self.pkg.is_epub3 else "2.0",
                "xmlns": "http://www.idpf.org/2007/opf",
                "unique-identifier": "pywebnovel-uid",
            },
        )
        pkg_element.appendChild(self.generate_metadata(dom, self.pkg))
        pkg_element.appendChild(self.generate_manifest(dom, self.pkg))
        pkg_element.appendChild(self.generate_spine(dom, self.pkg))
        pkg_element.appendChild(self.generate_guide(dom, self.pkg))
        self.data = dom.toxml(encoding="utf-8")


class Epub3Refs:
    """Epub3 References Tracker for Metadata."""

    dom: Document
    counter: int
    refs: list[Element]
    tag_id_fmt: str = "id-{counter:03d}"

    def __init__(self, dom: Document) -> None:
        self.counter = 0
        self.refs = []
        self.dom = dom

    def get_tag_id(self):
        """Generate a new tag id."""
        tag_id = self.tag_id_fmt.format(counter=self.counter)
        self.counter += 1
        return tag_id

    def add_ref(self, ref_type: str, ref_property: str, tag_id: str):
        """Add a new reference."""
        attributes = {"property": ref_property, "refines": f"#{tag_id}"}
        if ref_type in ("aut", "bkp"):
            attributes["scheme"] = "marc:relators"
        ref = create_element(self.dom, "meta", text=ref_type, attributes=attributes)
        self.refs.append(ref)


class TableOfContentsPage(EpubFileInterface):
    """The page containing the Table of Contents for the epub."""

    file_id: str = "toc_page"
    filename: str = "OEBPS/toc_page.xhtml"
    mimetype: str = "application/xhtml+xml"
    title: str = "Table of Contents"
    include_in_spine: bool = True
    include_in_manifest: bool = True
    data: bytes = None
    pkg: "EpubPackage" = None

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg

    def generate(self):
        """Generate TableOfContents Page."""
        items = []

        if self.pkg.files.cover_image:
            items.append(self.pkg.files.cover_image)

        if self.pkg.files.title_page:
            items.append(self.pkg.files.title_page)

        items += self.pkg.files.chapters
        template_kwargs = {"items": items}
        template = JINJA.get_template("toc_page.xhtml")
        self.data = template.render(**template_kwargs).encode("utf-8")


class ChapterFile(EpubFileInterface):
    """A file containing a chapter of the novel."""

    chapter: Chapter = None
    file_id: str = None
    filename: str = None
    mimetype: str = "application/xhtml+xml"
    title: str = None
    include_in_spine: bool = True
    include_in_manifest: bool = True
    data: bytes = None
    pkg: "EpubPackage" = None

    def __init__(self, pkg: "EpubPackage", chapter: Chapter, file_id: str) -> None:
        self.pkg = pkg
        self.chapter = chapter
        self.file_id = file_id
        self.filename = f"OEBPS/{self.file_id}.xhtml"
        self.title = chapter.title

    def generate(self):
        """Generate the XHTML file for a chapter."""
        template_kwargs = {
            "title": self.chapter.title,
            "url": self.chapter.url,
            "content": str(self.chapter.html_content),
        }
        template = JINJA.get_template("chapter.xhtml")
        self.data = template.render(**template_kwargs).encode("utf-8")


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
        """Generate nav.xhtml File."""
        template_kwargs = {
            "cover_page": self.pkg.files.cover_page,
            "toc": None,  # TODO
        }
        template = JINJA.get_template("nav.xhtml")
        self.data = template.render(**template_kwargs).encode("utf-8")
