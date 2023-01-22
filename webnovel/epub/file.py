"""Class representing the EPUB file."""

from dataclasses import dataclass
from xml.dom.minidom import getDOMImplementation, Element, Document
from typing import IO, Union
from zipfile import ZipFile, ZIP_STORED

from jinja2 import Environment, PackageLoader, select_autoescape, Template

from .data import EpubNovel
from ..data import Image, Novel
from ..utils import normalize_io


JINJA = Environment(loader=PackageLoader("webnovel.epub"), autoescape=select_autoescape())


def set_element_attributes(element: Element, attributes: dict) -> None:
    for name, value in attributes.items():
        element.setAttribute(name, value)


def create_element(dom: Document, name: str, text: str = None, attributes: dict = None, parent: Element = None):
    element = dom.createElement(name)

    if text is not None:
        text_node = dom.createTextNode(text)
        element.appendChild(text_node)

    set_element_attributes(element, attributes or {})

    if parent is not None:
        parent.appendChild(element)

    return element


class Epub3Refs:
    dom: Document
    counter: int
    refs: list[Element]
    tag_id_fmt: str = "id-{counter:03d}"

    def __init__(self, dom: Document) -> None:
        self.counter = 0
        self.refs = []
        self.dom = dom

    def get_tag_id(self):
        tag_id = self.tag_id_fmt.format(counter=self.counter)
        self.counter += 1
        return tag_id

    def add_ref(self, ref_type: str, ref_property: str, tag_id: str):
        attributes = {"property": ref_property, "refines": f"#{tag_id}"}
        if ref_type in ("aut", "bkp"):
            attributes["scheme"] = "marc:relators"
        ref = create_element(
            self.dom,
            "meta",
            text=ref_type,
            attributes=attributes,
        )
        self.refs.append(ref)


@dataclass
class EpubFile:
    file_id: str
    filename: str
    mimetype: str
    title: str = None
    include_in_spine: bool = False
    data: bytes = None


class TitlePage:
    """The title page of the epub."""

    file_id: str = "title_page"
    filename: str = "OEBPS/title_page.xhtml"
    mimetype: str = "application/xhtml+xml"
    title: str = "Title Page"
    include_in_spine: bool = True
    data: bytes = None
    title_page_css: str = "pywebnovel-titlepage"

    def generate(self, novel: Novel, stylesheet: str = "stylesheet.css"):
        template = JINJA.get_template("title_page.xhtml")
        self.data = template.render(novel=novel, stylesheet=stylesheet, title_page_css=self.title_page_css).encode("utf-8")


class PyWebNovelJSON:
    file_id: str = "pywebnovel-meta"
    filename: str = "pywebnovel.json"
    mimetype: str = "application/json"
    title: str = None
    include_in_spine: bool = False
    data: bytes = None


class CoverPage:
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


class TableOfContentsPage:
    """The page containing the Table of Contents for the epub."""

    file_id: str = "toc_page"
    filename: str = "OEBPS/toc_page.xhtml"
    mimetype: str = "application/xhtml+xml"
    title: str = "Table of Contents"
    include_in_spine: bool = True
    data: bytes = None

    def generate(self):
        pass


class EpubImage(EpubFile):
    image_id: str = None

    @classmethod
    def from_image(cls, image: Image, image_id: str) -> "EpubImage":
        return EpubImage(
            file_id=image_id,
            filename=f"OEBPS/{image_id}{image.extension}",
            mimetype=image.mimetype,
            data=image.data,
        )


class EpubImages(dict):
    image_id_counter: int
    cover_image: str = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image_id_counter = 0

    def validate(self) -> bool:
        return (
                len(self) <= self.image_id_counter
                and (self.cover_image is None or self.cover_image in self)
        )

    def generate_image_id(self):
        image_id = None
        while image_id is None or image_id in self:
            image_id = f"image{self.image_id_counter:03d}"
            self.image_id_counter += 1
        return image_id

    def add(self, image: Union[EpubImage, Image], is_cover_image: bool = False, force: bool = False) -> None:
        """
        Add an image to the image list.

        :param image: An EpubImage or Image instance to add to this list.
        :param is_cover_image: (optional) Should this image be set as the cover image. Default: False
        :param force: (optional) Control how to handle an image_id collision. Default: False
        """
        if isinstance(image, Image):
            image = EpubImage.from_image(image, image_id=self.generate_image_id())
        if image.file_id in self and not force:
            raise ValueError(f"EpubImageList: collision on key {image.file_id!r}")
        self[image.file_id] = image
        if is_cover_image:
            self.cover_image = image.file_id


class EpubManifest:
    is_epub3: bool
    include_title_page: bool
    include_toc_page: bool
    chapters: list
    images: EpubImages

    def __init__(self, is_epub3: bool = True, images: EpubImages = None, include_title_page: bool = True, include_toc_page: bool = True) -> None:
        self.is_epub3 = is_epub3
        self.include_title_page = include_title_page
        self.include_toc_page = include_toc_page
        self.chapters = []
        self.images = images

    def generate_file_list(self):
        files = [
            EpubFile(file_id="ncx", filename="toc.ncx", mimetype="application/x-dtbncx+xml"),
            EpubFile(file_id="style", filename="OEBPS/stylesheet.css", mimetype="text/css"),
            PyWebNovelJSON(),
        ]

        # TODO deal with images + cover image

        if self.include_title_page:
            files.append(TitlePage())

        if len(self.chapters) > 1 and self.include_toc_page:
            files.append(TableOfContentsPage())

        if self.images:
            for image_id, image in self.images.items():
                files.append(self.images[image_id])

            if self.images.cover_image:
                files.append(CoverPage())

        # TODO how to deal with chapter_url_map
        chapter_url_map = {}
        for index, chapter in enumerate(self.chapters):
            files.append(
                EpubFile(
                    file_id=f"ch{index:05d}",
                    filename=f"OEBPS/chapter_{index:05d}.xhtml",
                    mimetype="application/xhtml+xml",
                    title=chapter.title,
                    include_in_spine=True,
                )
            )
            chapter_url_map[chapter.url] = f"file{index:05d}.xhtml"

        return files

    def generate_manifest(self, dom: Document) -> Element:
        manifest = create_element(dom, "manifest")
        files = self.generate_file_list()

        for epub_file in files:
            create_element(
                dom,
                "item",
                attributes={"id": epub_file.file_id, "href": epub_file.filename, "media-type": epub_file.mimetype},
                parent=manifest,
            )

        if self.is_epub3:
            create_element(
                dom,
                "item",
                attributes={
                    "href": "nav.xhtml",
                    "id": "nav",
                    "media-type": "application/xhtml+xml",
                    "properties": "nav",
                },
                parent=manifest,
            )

        return manifest

    def generate_spine(self, dom: Document) -> Element:
        spine = create_element(dom, "spine", attributes={"toc": "ncx"})
        for epub_file in self.generate_file_list():
            if epub_file.include_in_spine and epub_file.file_id is not None:
                create_element(dom, "itemref", attributes={"idref": epub_file.file_id, "linear": "yes"}, parent=spine)
        return spine


class EpubPackage:
    filename: str
    novel: EpubNovel
    epub_version: str
    pkg_opf_path: str
    include_toc_page: bool
    include_title_page: bool
    default_language_code: str
    images: EpubImages
    include_images: bool

    def __init__(
        self,
        filename: str,
        novel: EpubNovel,
        default_language_code: str = "en",
        version: str = "3.0",
        pkg_opf_path: str = "package.opf",
        include_toc_page: bool = True,
        include_title_page: bool = True,
        include_images: bool = True,
    ) -> None:
        self.filename = filename
        self.novel = novel
        self.images = EpubImages()
        self.default_language_code = default_language_code
        self.epub_version = version
        self.pkg_opf_path = pkg_opf_path
        self.include_toc_page = include_toc_page
        self.include_title_page = include_title_page
        self.include_images = include_images

    @classmethod
    def load(cls, filename: str) -> "EpubPackage":
        pass  # TODO

    @property
    def is_epub3(self) -> bool:
        major_version, _, _ = str(self.epub_version).partition(".")
        return int(major_version) == 3

    @property
    def cover_image(self) -> EpubImage:
        return self.images[self.images.cover_image] if self.images.cover_image else None

    def get_container_xml(self) -> bytes:
        dom = getDOMImplementation().createDocument(None, "container", None)
        dom.documentElement.setAttribute("version", "1.0")
        dom.documentElement.setAttribute("xmlns", "urn:oasis:names:tc:opendocument:xmlns:container")
        root_files = dom.createElement("rootfiles")
        dom.documentElement.appendChild(root_files)
        root_file = dom.createElement("rootfile")
        root_file.setAttribute("full-path", self.pkg_opf_path)
        root_file.setAttribute("media-type", "application/oebps-package+xml")
        root_files.appendChild(root_file)
        return dom.toxml(encoding="utf-8")

    def generate_opf_metadata(self, dom: Document) -> Element:
        metadata = create_element(
            dom,
            "metadata",
            attributes={"xmlns:dc": "http://purl.org/dc/elements/1.1/", "xmlns:opf": "http://www.idpf.org/2007/opf"},
        )
        epub3_refs = Epub3Refs(dom)

        # TODO unique ID
        # epub_id = None
        # create_element(
        #     dom,
        #     "dc:identifier",
        #     text=epub_id,
        #     attributes={"id": "pywebnovel-uid"},
        #     parent=metadata,
        # )

        if self.novel.title:
            tag_id = epub3_refs.get_tag_id()
            create_element(dom, "dc:title", text=self.novel.title, attributes={"id": tag_id}, parent=metadata)
            epub3_refs.add_ref(
                ref_type="main",
                ref_property="title-type",
                tag_id=tag_id,
            )

        if self.novel.author:
            # TODO support list of authors
            tag_id = epub3_refs.get_tag_id()
            create_element(
                dom,
                "dc:creator",
                text=self.novel.author.name,
                attributes={"id": tag_id} if self.is_epub3 else {"opf:role": "aut"},
                parent=metadata
            )
            epub3_refs.add_ref(
                ref_type="aut",
                tag_id=tag_id,
                ref_property="role",
            )

        tag_id = epub3_refs.get_tag_id()
        create_element(
            dom,
            "dc:contributor",
            text="PyWebnovel [https://github.com/bsandrow/PyWebnovel]",
            attributes={"id": tag_id},
            parent=metadata,
        )
        epub3_refs.add_ref(
            ref_type="bkp",
            ref_property="role",
            tag_id=tag_id,
        )

        # TODO add language_code to Novel
        langcode = "en"
        create_element(dom, "dc:language", text=langcode, parent=metadata)

        # TODO published / created / updated / calibre (add to Novel)

        if self.novel.summary:
            create_element(dom, "dc:description", text=self.novel.summary, parent=metadata)

        if self.novel.genres:
            for genre in self.novel.genres:
                create_element(dom, "dc:subject", text=genre, parent=metadata)

        # TODO site

        # Novel URL
        create_element(
            dom,
            "dc:identifier",
            text=f"URL:{self.novel.url}" if self.is_epub3 else self.novel.url,
            attributes=None if self.is_epub3 else {"opf:scheme": "URL"},
            parent=metadata,
        )
        create_element(dom, "dc:source", text=self.novel.url, parent=metadata)

        if self.cover_image:
            # <meta name="cover" content="$COVER_IMAGE_ID"/>
            create_element(
                dom, "meta", parent=metadata, attributes={"name": "cover", "content": self.cover_image.file_id}
            )

        if self.is_epub3:
            for ref in epub3_refs.refs:
                metadata.appendChild(ref)

        return metadata

    def get_package_opf(self) -> bytes:
        dom = getDOMImplementation().createDocument(None, "package", None)
        pkg_element = dom.documentElement
        set_element_attributes(
            pkg_element,
            {
                "version": "3.0" if self.is_epub3 else "2.0",
                "xmlns": "http://www.idpf.org/2007/opf",
                "unique-identifier": "pywebnovel-uid",
            }
        )
        metadata = self.generate_opf_metadata(dom)
        pkg_element.appendChild(metadata)

        manifest = EpubManifest(is_epub3=self.is_epub3)
        pkg_element.appendChild(manifest.generate_manifest(dom))
        pkg_element.appendChild(manifest.generate_spine(dom))

        return dom.toxml(encoding="utf-8")

    def save(self, file_or_io: Union[str, IO]) -> IO:
        zipio = normalize_io(file_or_io, "wb")
        zipfile = ZipFile(zipio, "w", compression=ZIP_STORED)
        zipfile.writestr("mimetype", b"application/epub+zip")
        zipfile.writestr("META-INF/container.xml", self.get_container_xml())
        zipfile.writestr(self.pkg_opf_path, self.get_package_opf())
        for _, image in self.images.items():
            zipfile.writestr(image.filename, image.data)
        zipfile.close()
        return zipio
