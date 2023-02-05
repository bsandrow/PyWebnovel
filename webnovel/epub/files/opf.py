
from xml.dom.minidom import Document, Element, getDOMImplementation
from typing import Optional, TYPE_CHECKING

from webnovel.epub.files import EpubImages, EpubFileInterface, BasicFileInterface, PyWebNovelJSON, CoverPage
from webnovel.xml import create_element, set_element_attributes

if TYPE_CHECKING:
    from webnovel.epub.pkg import EpubPackage


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

    def generate_file_list(self) -> list[EpubFileInterface]:
        files = [
            NavigationControlFile(),
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


class PackageOPF(BasicFileInterface):
    filename: str = "package.opf"
    data: bytes = None

    def __init__(self, filename: str = None):
        self.filename = filename or self.filename

    @staticmethod
    def generate_guide(dom: Document, pkg: "EpubPackage") -> Optional[Element]:
        """
        Generate <guide> element for PackageOPF file.

        Only generated if there is a cover image and include_images=True for the parent package.
        """
        if pkg.include_images and pkg.cover_image:
            guide = create_element(dom, "guide")
            create_element(dom, "reference", parent=guide, attributes={
                "type": "cover", "title": "Cover", "href": CoverPage.filename
            })
            return guide
        return None

    @staticmethod
    def generate_spine(dom: Document, pkg: "EpubPackage") -> Element:
        spine = create_element(dom, "spine", attributes={"toc": "ncx"})
        for epub_file in pkg.files:
            if epub_file.include_in_spine and epub_file.file_id is not None:
                create_element(dom, "itemref", attributes={"idref": epub_file.file_id, "linear": "yes"}, parent=spine)
        return spine

    @staticmethod
    def generate_manifest(dom: Document, pkg: "EpubPackage") -> Element:
        manifest = create_element(dom, "manifest")

        for epub_file in pkg.files:
            create_element(
                dom,
                "item",
                attributes={
                    "id": epub_file.file_id,
                    "href": epub_file.filename,
                    "media-type": epub_file.mimetype
                },
                parent=manifest,
            )

        if pkg.is_epub3:
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

    @staticmethod
    def generate_metadata(dom: Document, pkg: "EpubPackage") -> Element:
        metadata = create_element(
            dom,
            "metadata",
            attributes={
                "xmlns:dc": "http://purl.org/dc/elements/1.1/",
                "xmlns:opf": "http://www.idpf.org/2007/opf"
            },
        )
        epub3_refs = Epub3Refs(dom)
        create_element(dom, "dc:identifier", text=pkg.epub_uid, attributes={"id": "pywebnovel-uid"}, parent=metadata)

        if pkg.novel.title:
            tag_id = epub3_refs.get_tag_id()
            create_element(dom, "dc:title", text=pkg.novel.title, attributes={"id": tag_id}, parent=metadata)
            epub3_refs.add_ref(
                ref_type="main",
                ref_property="title-type",
                tag_id=tag_id,
            )

        if pkg.novel.author:
            # TODO support list of authors
            tag_id = epub3_refs.get_tag_id()
            create_element(
                dom,
                "dc:creator",
                text=pkg.novel.author.name,
                attributes={"id": tag_id} if pkg.is_epub3 else {"opf:role": "aut"},
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

        if pkg.include_images and pkg.cover_image:
            # <meta name="cover" content="$COVER_IMAGE_ID"/>
            create_element(
                dom,
                "meta",
                parent=metadata,
                # Note: Order matters here for some broken ereader implementations (i.e. "name" must come before
                #       "content")
                attributes={"name": "cover", "content": pkg.cover_image.file_id}
            )

        if pkg.is_epub3:
            for ref in epub3_refs.refs:
                metadata.appendChild(ref)

        return metadata

    def generate(self, pkg: "EpubPackage") -> None:
        dom = getDOMImplementation().createDocument(None, "package", None)
        pkg_element = dom.documentElement
        set_element_attributes(
            pkg_element,
            {
                "version": "3.0" if pkg.is_epub3 else "2.0",
                "xmlns": "http://www.idpf.org/2007/opf",
                "unique-identifier": "pywebnovel-uid",
            }
        )
        pkg_element.appendChild(self.generate_metadata(dom, pkg))
        pkg_element.appendChild(self.generate_manifest(dom, pkg))
        pkg_element.appendChild(self.generate_spine(dom, pkg))
        pkg_element.appendChild(self.generate_guide(dom, pkg))
        self.data = dom.toxml(encoding="utf-8")



