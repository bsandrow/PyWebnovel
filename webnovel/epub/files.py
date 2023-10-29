"""Classes to represent and generate the files that will be in the epub package."""

from dataclasses import asdict, dataclass, is_dataclass
import datetime
import inspect
import json
from pathlib import Path
import pkgutil
import posixpath
import sys
from typing import TYPE_CHECKING, Iterable, Union
from xml.dom.minidom import Document, Element, getDOMImplementation
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from bs4 import BeautifulSoup, Tag
import jinja2

from webnovel.data import Chapter, Image
from webnovel.epub.data import SummaryType
from webnovel.utils import filter_dict
from webnovel.xml import create_element, set_element_attributes

if TYPE_CHECKING:
    from webnovel.epub.pkg import EpubPackage


JINJA = jinja2.Environment(
    # loader=jinja2.PackageLoader("webnovel.epub", package_path="content/templates"),
    loader=jinja2.FunctionLoader(
        lambda name: pkgutil.get_data("webnovel.epub", f"content/templates/{name}").decode("utf-8")
    ),
    autoescape=jinja2.select_autoescape(),
)


def generate_toc_list(pkg: "EpubPackage"):
    """
    Generate the list of files for the Table of Contents.

    Files will be included/excluded depending on if they are a part of the epub file passed in.
    """
    toc_files = []
    if pkg.cover_page:
        toc_files.append(pkg.cover_page)
    if pkg.title_page:
        toc_files.append(pkg.title_page)
    if pkg.toc_page:
        toc_files.append(pkg.toc_page)
    toc_files += sorted(pkg.chapter_files, key=lambda chfile: chfile.file_id)
    return toc_files


def from_dict_to_file(data: dict) -> "EpubInternalFile":
    """Turn a dict into an instance of the proper file based on some information like file_id."""
    file_class_map = {
        obj.file_id: obj
        for _, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass)
        if obj.__module__ is __name__
        and issubclass(obj, EpubInternalFile)
        and hasattr(obj, "file_id")
        and obj.file_id is not None
    }

    assert "file_id" in data
    file_class = file_class_map.get(data["file_id"])

    if file_class:
        return file_class.from_dict(data)

    if "chapter_id" in data:
        return ChapterFile.from_dict(data)

    if "mimetype" in data and data["mimetype"].startswith("image/"):
        return ImageFile.from_dict(data)

    raise ValueError(f"Unable to find file class for: {data}")


class EpubInternalFile:
    """The base class for all epub internal files."""

    file_id: str
    filename: str
    mimetype: str
    title: str | None = None
    compress_type: int = ZIP_STORED

    @property
    def parent(self) -> str:
        """Return the path to the directory this file is in."""
        return str(Path(self.filename).parent)

    def __eq__(self, other) -> bool:
        """Compare two EpubInternalFiles."""
        return (
            isinstance(other, self.__class__)
            and self.file_id == other.file_id
            and self.filename == other.filename
            and self.mimetype == other.mimetype
            and self.title == other.title
            and self.compress_type == other.compress_type
            and self.to_dict() == other.to_dict()
        )

    def to_dict(self) -> dict:
        """Convert an EpubInternalFile into a dict."""
        return {
            "file_id": self.file_id,
            "filename": self.filename,
            "mimetype": self.mimetype,
            "title": self.title,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EpubInternalFile":
        """Create an instance from a dict."""
        assert "file_id" in data
        assert "filename" in data or cls.filename is not None
        assert "mimetype" in data or cls.mimetype is not None
        assert not hasattr(cls, "file_id") or cls.file_id is None or cls.file_id == data["file_id"]

        kwargs = {}

        if cls.file_id is None and "file_id" in data:
            kwargs["file_id"] = data["file_id"]

        for key in ("filename", "mimetype", "title"):
            if key in data:
                kwargs[key] = data[key]

        return cls(**kwargs)

    def relative_to(self, path: Union[str, Path]) -> str:
        """Return a path for this file that's relative to the provided path."""
        return posixpath.relpath(self.filename, str(path))

    def generate(self, pkg: "EpubPackage") -> bytes:
        """Return the contents of the file as bytes."""
        raise NotImplementedError

    def write(self, pkg: "EpubPackage", zipfile: ZipFile) -> None:
        """Write the file contents to a zipfile."""
        zipfile.writestr(self.filename, self.generate(pkg), compress_type=self.compress_type)


class SingleFileMixin:
    """Mixin that overrides from_dict() for files that have static attribute values (like file_id and filename)."""

    @classmethod
    def from_dict(cls, data: dict):
        """Create a new instance if the file_id and filename match up."""
        assert data["file_id"] == cls.file_id
        assert data["filename"] == cls.filename
        return cls()


class ImageFile(EpubInternalFile):
    """An image file in the epub package."""

    file_id: str = None
    filename: str
    mimetype: str
    title = None
    is_cover_image: bool = False

    def __init__(
        self,
        file_id: str,
        mimetype: str,
        extension: str | None = None,
        filename: str | None = None,
        is_cover_image: bool = False,
    ) -> None:
        # TODO use imghdr to make mimetype optional
        # TODO use imghdr to fallback of mimetype lookup fails
        self.file_id = file_id
        self.mimetype = mimetype
        self.is_cover_image = is_cover_image
        if not extension and not filename:
            extension = Image.extension_map[mimetype.lower()]
        self.filename = filename or f"OEBPS/Images/{file_id}{extension}"

    @classmethod
    def from_dict(cls, data: dict) -> "ImageFile":
        """Turn a dict into an ImageFile."""
        return cls(**filter_dict(data, ["file_id", "filename", "mimetype", "is_cover_image"]))

    def to_dict(self) -> dict:
        """Turn an ImageFile into a dict."""
        return {name: getattr(self, name) for name in ["file_id", "filename", "mimetype", "is_cover_image"]}

    def generate(self, pkg):
        """Return the image contents from EpubPackage.image_map."""
        # TODO support URLs here too?
        image_data: bytes = pkg.image_map[self.file_id]
        return image_data


class MimetypeFile(SingleFileMixin, EpubInternalFile):
    """
    A simple file containing the mimetype of the epub package.

    It's part of the spec to have a file called 'mimetype' with a just the
    mimetype as the contents.
    """

    file_id: str = "mimetype"
    filename: str = "mimetype"
    mimetype: str = ""

    def generate(self, pkg):
        """Return contents of the mimetype file."""
        return b"application/epub+zip"


class ContainerXML(SingleFileMixin, EpubInternalFile):
    """
    A Top-Level XML File in the Epub Format.

    This file basically only exists to specify the name and location of the
    package.opf file.  Technically that file doesn't need to be named
    package.opf and could be anywhere in the file structure, so long as this
    file points to it correctly.
    """

    file_id: str = "container-xml"
    filename: str = "META-INF/container.xml"
    mimetype: str = ""

    def generate(self, pkg):
        """Generate the contents of this XML file into data attribute."""
        dom = getDOMImplementation().createDocument(None, "container", None)
        dom.documentElement.setAttribute("version", "1.0")
        dom.documentElement.setAttribute("xmlns", "urn:oasis:names:tc:opendocument:xmlns:container")
        root_files = dom.createElement("rootfiles")
        dom.documentElement.appendChild(root_files)
        root_file = dom.createElement("rootfile")
        root_file.setAttribute("full-path", "OEBPS/content.opf")
        root_file.setAttribute("media-type", "application/oebps-package+xml")
        root_files.appendChild(root_file)
        return dom.toxml(encoding="utf-8")


class Stylesheet(SingleFileMixin, EpubInternalFile):
    """The stylesheet for the ereader to use in rendering."""

    file_id: str = "style"
    filename: str = "OEBPS/stylesheet.css"
    mimetype: str = "text/css"

    def generate(self, pkg):
        """Load the stylesheet data from embeded stylesheet."""
        data = pkgutil.get_data("webnovel.epub", "content/stylesheet.css")
        if pkg.extra_css:
            data += b"\n\n" + pkg.extra_css.encode("utf-8")
        return data


class NavigationControlFile(SingleFileMixin, EpubInternalFile):
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
    filename: str = "OEBPS/toc.ncx"
    mimetype: str = "application/x-dtbncx+xml"

    def generate(self, pkg):
        """Generate XML Contents into data attribute."""
        parent = Path(self.filename).parent
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

        create_element(dom, "meta", parent=head, attributes={"name": "dtb:uid", "content": pkg.epub_uid})
        create_element(dom, "meta", parent=head, attributes={"name": "dtb:depth", "content": "1"})
        create_element(dom, "meta", parent=head, attributes={"name": "dtb:totalPageCount", "content": "0"})
        create_element(dom, "meta", parent=head, attributes={"name": "dtb:maxPageNumber", "content": "0"})
        create_element(dom, "text", parent=doc_title, text=pkg.metadata.title)

        for index, epub_file in enumerate(generate_toc_list(pkg)):
            nav_point_node = create_element(
                dom, "navPoint", parent=navmap_node, attributes={"id": epub_file.file_id, "playOrder": str(index)}
            )
            nav_label = create_element(dom, "navLabel", parent=nav_point_node)
            create_element(dom, "text", parent=nav_label, text=epub_file.title)
            create_element(dom, "content", parent=nav_point_node, attributes={"src": epub_file.relative_to(parent)})

        return dom.toxml(encoding="utf-8")


class TitlePage(SingleFileMixin, EpubInternalFile):
    """The title page of the epub."""

    file_id: str = "title_page"
    filename: str = "OEBPS/Text/title_page.xhtml"
    mimetype: str = "application/xhtml+xml"
    title: str = "Title Page"
    title_page_css: str = "pywebnovel-titlepage"

    def generate(self, pkg):
        """Generate title page XHMTL file."""
        parent = Path(self.filename).parent
        template_kwargs = {
            "now": datetime.datetime.now(),
            "strftime": datetime.datetime.strftime,
            "novel": pkg.metadata,
            "stylesheet": pkg.stylesheet.relative_to(parent),
            "title_page_css": self.title_page_css,
            "author_name": None,
            "author_url": None,
            "items": {},
            "credits": {},
            "summary_html": None,
            "summary_text": None,
        }

        # Summary
        if pkg.metadata.summary_type == SummaryType.html:
            template_kwargs["summary_html"] = pkg.metadata.summary
        if pkg.metadata.summary_type == SummaryType.text:
            template_kwargs["summary_text"] = pkg.metadata.summary

        # Credits
        if pkg.metadata.author is not None:
            template_kwargs["credits"]["Author"] = pkg.metadata.author

        if pkg.metadata.translator is not None:
            template_kwargs["credits"]["Translator"] = pkg.metadata.translator

        # General Information
        items = template_kwargs["items"]
        items["Publisher"] = pkg.metadata.site_id
        items["Chapter Count"] = len(pkg.chapters)

        if pkg.metadata.published_on:
            items["Published On"] = pkg.metadata.published_on.strftime("%b %-d, %Y")

        if pkg.metadata.last_updated_on:
            items["Novel Last Updated On"] = pkg.metadata.last_updated_on.strftime("%b %-d, %Y")

        if pkg.metadata.genres:
            items["Genres"] = ", ".join(pkg.metadata.genres)

        if pkg.metadata.status:
            items["Status"] = pkg.metadata.status.value

        if pkg.metadata.tags:
            items["Tags"] = ", ".join(pkg.metadata.tags)

        if pkg.metadata.extras:
            for title, value in pkg.metadata.extras.items():
                if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
                    items[title] = ", ".join(value)
                elif isinstance(value, datetime.datetime):
                    items[title] = value.strftime("%b %d, %Y")
                else:
                    items[title] = str(value)

        template = JINJA.get_template("title_page.xhtml")
        return template.render(**template_kwargs).encode("utf-8")


class CoverPage(SingleFileMixin, EpubInternalFile):
    """The cover page (containing the cover image) of the epub."""

    file_id: str = "cover"
    filename: str = "OEBPS/Text/cover.xhtml"
    mimetype: str = "application/xhtml+xml"
    title: str = "Cover"

    def generate(self, pkg):
        """Generate cover page XHTML."""
        parent = Path(self.filename).parent
        template_kwargs = {
            "lang": "en",
            "stylesheet": pkg.stylesheet.relative_to(parent),
            "title": pkg.metadata.title,
            "cover_image_path": pkg.cover_image.relative_to(parent),
        }
        template = JINJA.get_template("cover.xhtml")
        return template.render(**template_kwargs).encode("utf-8")


class TableOfContentsPage(SingleFileMixin, EpubInternalFile):
    """The page containing the Table of Contents for the epub."""

    file_id: str = "toc_page"
    filename: str = "OEBPS/Text/toc_page.xhtml"
    mimetype: str = "application/xhtml+xml"
    title: str = "Contents"

    def generate(self, pkg):
        """Generate TableOfContents Page."""
        parent = Path(self.filename).parent
        template_kwargs = {
            "title": pkg.metadata.title + (f" by {pkg.metadata.author.name}" if pkg.metadata.author else ""),
            "stylesheet": pkg.stylesheet.relative_to(parent),
            "items": [{"title": item.title, "filename": item.relative_to(parent)} for item in generate_toc_list(pkg)],
        }
        template = JINJA.get_template("toc_page.xhtml")
        return template.render(**template_kwargs).encode("utf-8")


class ChapterFile(EpubInternalFile):
    """A file containing a chapter of the novel."""

    chapter_id: str
    file_id: str
    filename: str
    mimetype: str = "application/xhtml+xml"
    title: str = None

    def __init__(self, chapter_id: str, file_id: str, filename: str | None = None, title: str | None = None) -> None:
        self.chapter_id = chapter_id
        self.file_id = file_id
        self.filename = filename or f"OEBPS/Text/{self.file_id}.xhtml"
        self.title = title or chapter_id

    @classmethod
    def from_dict(cls, data: dict) -> "ChapterFile":
        """Turn a dict into a ChapterFile."""
        assert "chapter_id" in data
        assert "file_id" in data
        return ChapterFile(**filter_dict(data, ("chapter_id", "file_id", "filename", "title")))

    def to_dict(self) -> dict:
        """Turn a ChapterFile into a dict."""
        return {
            "chapter_id": self.chapter_id,
            "file_id": self.file_id,
            "mimetype": self.mimetype,
            "filename": self.filename,
            "title": self.title,
        }

    def get_chapter(self, pkg: "EpubPackage") -> Chapter:
        """Return the Chapter instance by looking it up in the EpubPackage chapter map."""
        return pkg.chapters[self.chapter_id]

    def generate(self, pkg):
        """Generate the XHTML file for a chapter."""
        chapter = self.get_chapter(pkg)
        parent = Path(self.filename).parent
        content = str(chapter.html)

        if pkg.include_images:
            for image_file in pkg.images:
                content = content.replace(f"IMAGE:{image_file.file_id}", image_file.relative_to(self.parent))

        template_kwargs = {
            "title": self.title or chapter.title,
            "url": chapter.url,
            "stylesheet": pkg.stylesheet.relative_to(parent),
            "content": content,
            "css": None,
            "lang": "en",
        }
        template = JINJA.get_template("chapter.xhtml")
        return template.render(**template_kwargs).encode("utf-8")


class NavXhtml(SingleFileMixin, EpubInternalFile):
    """Class for the nav.xhtml file."""

    file_id: str = "nav"
    filename: str = "OEBPS/Text/nav.xhtml"
    mimetype: str = "application/xhtml+xml"
    title: str = None

    def generate(self, pkg):
        """Generate nav.xhtml File."""
        parent = Path(self.filename).parent
        template_kwargs = {
            "title": pkg.metadata.title,
            "file_id": self.file_id,
            "lang": "en",
            "cover_page": (pkg.cover_page.relative_to(parent) if pkg.cover_page else None),
            "stylesheet": pkg.stylesheet.relative_to(parent),
            "toc_page": (pkg.toc_page.relative_to(parent) if pkg.toc_page else None),
            "toc": [(item.title, item.relative_to(parent)) for item in generate_toc_list(pkg)],
        }
        template = JINJA.get_template("nav.xhtml")
        return template.render(**template_kwargs).encode("utf-8")


class Epub3Refs:
    """Epub3 References Tracker for Metadata."""

    dom: Document
    counter: int
    refs: list[Element]
    tag_id_fmt: str = "id-{counter:03d}"

    # Reference: https://idpf.org/epub/20/spec/OPF_2.0_final_spec.html#TOC2.2.6
    types = {
        "adapter": "adp",
        "annotator": "ann",
        "arranger": "arr",
        "artist": "art",
        "associated name": "asn",
        "author": "aut",
        "author in quotations or text extracts": "aqt",
        "author of afterword, colophon, etc.": "aft",
        "author of introduction, etc.": "aui",
        "bibliographic antecedent": "ant",
        "book producer": "bkp",
        "collaborator": "clb",
        "commentator": "cmm",
        "designer": "dsr",
        "editor": "edt",
        "illustrator": "ill",
        "lyricist": "lyr",
        "metadata contact": "mdc",
        "musician": "mus",
        "narrator": "nrt",
        "other": "oth",
        "photographer": "pht",
        "printer": "prt",
        "redactor": "red",
        "reviewer": "rev",
        "sponsor": "spn",
        "thesis advisor": "ths",
        "transcriber": "trc",
        "translator": "trl",
    }

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


class PackageOPF(SingleFileMixin, EpubInternalFile):
    """The Main XML file that acts as a manifest for the epub package."""

    file_id: str = "opf"
    filename: str = "OEBPS/content.opf"
    mimetype: str = ""

    @staticmethod
    def generate_guide(dom: Document, pkg: "EpubPackage", path: str) -> Element | None:
        """
        Generate <guide> element for PackageOPF file.

        Only generated if there is a cover image and include_images=True for the parent package.
        """
        guide = create_element(dom, "guide")
        start_page = pkg.chapter_files[0] if len(pkg.chapter_files) > 0 else None

        if toc_page := pkg.toc_page:
            start_page = toc_page
            attrs = {"type": "toc", "title": "Table of Contents", "href": str(toc_page.relative_to(path))}
            create_element(dom, "reference", parent=guide, attributes=attrs)

        if title_page := pkg.title_page:
            start_page = title_page

        if pkg.include_images and (cover_page := pkg.cover_page):
            start_page = cover_page
            attrs = {"type": "cover", "title": "Cover", "href": str(cover_page.relative_to(path))}
            create_element(dom, "reference", parent=guide, attributes=attrs)

        if start_page:
            attrs = {"type": "start", "title": "Begin Reading", "href": str(start_page.relative_to(path))}
            create_element(dom, "reference", parent=guide, attributes=attrs)

        return guide

    @staticmethod
    def generate_spine(dom: Document, pkg: "EpubPackage") -> Element:
        """Generate a <spine> for the OPF package."""
        spine = create_element(dom, "spine", attributes={"toc": "ncx"})
        for spine_item in generate_toc_list(pkg):
            create_element(dom, "itemref", attributes={"idref": spine_item.file_id, "linear": "yes"}, parent=spine)
        return spine

    @staticmethod
    def get_manifest_file_list(pkg: "EpubPackage") -> list[EpubInternalFile]:
        """Return the list of files to add to the <manifest>."""
        return [
            epub_file
            for epub_file in (
                [pkg.cover_page, pkg.title_page, pkg.toc_page]
                + pkg.chapter_files
                + [pkg.ncx, pkg.stylesheet]
                + ([pkg.nav] if pkg.is_epub3 else [])
                + pkg.images
            )
            if epub_file is not None
        ]

    @staticmethod
    def generate_manifest(dom: Document, pkg: "EpubPackage", path: str) -> Element:
        """Generate a <manifest> for the OPF package."""
        manifest = create_element(dom, "manifest")

        for epub_file in PackageOPF.get_manifest_file_list(pkg):
            attrs = {
                "id": epub_file.file_id,
                "href": str(epub_file.relative_to(path)),
                "media-type": epub_file.mimetype,
            }

            if epub_file == pkg.cover_image:
                attrs["properties"] = "cover-image"

            if epub_file == pkg.nav:
                attrs["properties"] = "nav"

            create_element(dom, "item", attributes=attrs, parent=manifest)

        return manifest

    @staticmethod
    def generate_metadata(dom: Document, pkg: "EpubPackage") -> Element:
        """Generate the <metadata> for the novel."""
        attrs = {"xmlns:dc": "http://purl.org/dc/elements/1.1/", "xmlns:opf": "http://www.idpf.org/2007/opf"}
        metadata = create_element(dom, "metadata", attributes=attrs)
        epub3_refs = Epub3Refs(dom)
        create_element(dom, "dc:identifier", text=pkg.epub_uid, attributes={"id": "pywebnovel-uid"}, parent=metadata)

        if pkg.is_epub3:
            create_element(
                dom,
                "meta",
                attributes={"property": "dcterms:modified"},
                text=datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                parent=metadata,
            )
            if pkg.metadata.published_on:
                create_element(
                    dom, "dc:date", text=pkg.metadata.published_on.strftime("%Y-%m-%dT00:00:00Z"), parent=metadata
                )

        #
        # Set the site this was scraped from as the publisher.
        #
        create_element(dom, "dc:publisher", text=pkg.metadata.site_id, parent=metadata)

        # else:
        #     if pkg.metadata.published_on:
        #         create_element(dom, "dc:date", attributes={"opf:event": "publication"}, text=pkg.metadata.published_on.strftime("%Y-%m-%dT00:00:00Z"))
        #     if pkg.metadata.created_on:
        #         create_element(dom, "dc:date", attributes={"opf:event": "creation"}, text=pkg.metadata.created_on.strftime("%Y-%m-%d"))
        #     if pkg.metadata.updated_on:
        #         create_element(dom, "dc:date", attributes={"opf:event": "modification"}, text=pkg.metadata.updated_on.strftime("%Y-%m-%dT00:00:00Z"))
        #         create_element(dom, "meta", attributes={"name": "calibre:timestamp", "content": pkg.metadata.updated_on.strftime("%Y-%m-%d")}, text=pkg.metadata.updated_on.strftime("%Y-%m-%d"))

        if pkg.metadata.title:
            tag_id = epub3_refs.get_tag_id()
            create_element(dom, "dc:title", text=pkg.metadata.title, attributes={"id": tag_id}, parent=metadata)
            epub3_refs.add_ref(ref_type="main", ref_property="title-type", tag_id=tag_id)

        if pkg.metadata.author:
            # TODO support list of authors
            tag_id = epub3_refs.get_tag_id()
            if pkg.is_epub3:
                create_element(
                    dom, "dc:creator", text=pkg.metadata.author.name, attributes={"id": tag_id}, parent=metadata
                )
            else:
                create_element(
                    dom, "dc:creator", text=pkg.metadata.author.name, attributes={"opf:role": "aut"}, parent=metadata
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

        if pkg.metadata.summary:
            if pkg.metadata.summary_type == SummaryType.html:
                summary = BeautifulSoup(pkg.metadata.summary, "html.parser").text
            else:
                summary = pkg.metadata.summary
            create_element(dom, "dc:description", text=summary, parent=metadata)

        if pkg.metadata.genres:
            for genre in pkg.metadata.genres + ["PyWebnovel", "Webnovel"]:
                create_element(dom, "dc:subject", text=genre, parent=metadata)

        # TODO site

        # TODO calibre-specific metadata:
        #
        #       <meta name="calibre:series" content="" />
        #       <meta name="calibre:series_index" content="" />
        #
        #       EPUB3
        #       <meta id="series" property="belongs-to-collection">Series Name</dc:title>
        #       <meta refines="#series" property="collection-type">series</meta>
        #       <meta refines="#series" property="group-position">1</meta>

        # Novel URL
        create_element(
            dom,
            "dc:identifier",
            text=f"URL:{pkg.metadata.novel_url}" if pkg.is_epub3 else pkg.metadata.novel_url,
            attributes=None if pkg.is_epub3 else {"opf:scheme": "URL"},
            parent=metadata,
        )
        create_element(dom, "dc:source", text=pkg.metadata.novel_url, parent=metadata)

        if pkg.include_images and pkg.cover_page:
            # <meta name="cover" content="$COVER_IMAGE_ID"/>
            # Note: Order matters here for some broken ereader implementations (i.e. "name" must come before
            #       "content")
            attrs = {"name": "cover", "content": pkg.cover_image.file_id}
            create_element(dom, "meta", parent=metadata, attributes=attrs)

        if pkg.is_epub3:
            for ref in epub3_refs.refs:
                metadata.appendChild(ref)

        return metadata

    def generate(self, pkg):
        """Generate package.opf file."""
        dom = getDOMImplementation().createDocument(None, "package", None)
        parent_path = Path(self.filename).parent
        pkg_element = dom.documentElement
        set_element_attributes(
            pkg_element,
            {
                "version": "3.0" if pkg.is_epub3 else "2.0",
                "xmlns": "http://www.idpf.org/2007/opf",
                "unique-identifier": "pywebnovel-uid",
            },
        )
        pkg_element.appendChild(self.generate_metadata(dom, pkg))
        pkg_element.appendChild(self.generate_manifest(dom, pkg, parent_path))
        pkg_element.appendChild(self.generate_spine(dom, pkg))
        pkg_element.appendChild(self.generate_guide(dom, pkg, parent_path))
        return dom.toxml(encoding="utf-8")


class PyWebNovelJSON(SingleFileMixin, EpubInternalFile):
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
    compress_type: int = ZIP_DEFLATED

    class JSONEncoder(json.JSONEncoder):
        def default(self, item):
            """Handle dataclasses automatically."""
            from enum import Enum

            if hasattr(item, "to_dict") and inspect.ismethod(item.to_dict):
                return item.to_dict()
            if is_dataclass(item):
                return asdict(item)
            if isinstance(item, datetime.date) and not isinstance(item, datetime.datetime):
                return item.strftime("%Y-%m-%d")
            if isinstance(item, datetime.date) and isinstance(item, datetime.datetime):
                return item.strftime("%Y-%m-%d %H:%M")
            if isinstance(item, Enum):
                return item.value
            return super().default(item)

    def generate(self, pkg):
        """Serialize the novel information into the data attribute as JSON."""
        return json.dumps(
            {
                "epub_uid": pkg.epub_uid,
                "metadata": pkg.metadata.to_dict(),
                "options": pkg.options.to_dict(),
                "files": pkg.file_map,
                "chapters": pkg.chapters,
                "extra_css": pkg.extra_css,
            },
            cls=self.JSONEncoder,
        ).encode("utf-8")

    @classmethod
    def load_from_pkg(cls, pkg: ZipFile) -> dict:
        """Load a PyWebNovelJSON from a ZipFile instance."""
        raw_data = pkg.read(cls.filename)
        return json.loads(raw_data)


class Changelog(EpubInternalFile):
    """
    A file that lists all of the changes to the ebook since (and including) creation.

    The "true" log is stored in the application json file. This logfile will
    always be regenerated from the true log.
    """

    file_id: str = "changelog"
    filename: str = "OEBPS/Text/changelog.xhtml"
    mimetype: str = "application/xhtml+xml"
    title: str = "Changelog"

    def generate(self, pkg):
        """Generate the logfile."""
        template_kwargs = {}
        template = JINJA.get_template("changelog.xhtml")
        return template.render(**template_kwargs).encode("utf-8")
