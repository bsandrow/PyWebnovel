"""Class representing the EPUB file."""

from dataclasses import dataclass
import hashlib
from inspect import isclass
from io import BytesIO
import logging
from pathlib import Path
from typing import IO, Optional, Union
from zipfile import ZIP_STORED, ZipFile

from webnovel.data import Chapter, Image, Novel
from webnovel.epub.data import EpubMetadata, EpubOptions
from webnovel.epub.files import (
    ChapterFile,
    ContainerXML,
    CoverPage,
    EpubInternalFile,
    ImageFile,
    MimetypeFile,
    NavigationControlFile,
    NavXhtml,
    PackageOPF,
    PyWebNovelJSON,
    Stylesheet,
    TableOfContentsPage,
    TitlePage,
    from_dict_to_file,
)

from ..utils import filter_dict, normalize_io

logger = logging.getLogger(__name__)


class EpubPackage:
    """A representation of an epub ebook file."""

    epub_uid: str
    options: EpubOptions
    metadata: EpubMetadata
    file_map: dict[str, EpubInternalFile]
    image_map: dict[str, bytes]
    chapters: dict[str, Chapter]
    extra_css: Optional[str] = None
    pkg_opf_path: str = "OEBPS/content.opf"
    cover_image_id: Optional[str] = None

    def __init__(
        self,
        options: Union[EpubOptions, dict],
        metadata: Union[EpubMetadata, Novel, dict],
        epub_uid: Optional[str] = None,
        files: Optional[dict[str, EpubInternalFile]] = None,
        file_or_io: Optional[Union[str, IO]] = None,
        extra_css: Optional[str] = None,
        chapters: Optional[dict[Chapter]] = None,
        cover_image_id: Optional[str] = None,
    ) -> None:
        self.zipio = normalize_io(file_or_io, "wb")
        self.metadata = (
            EpubMetadata.from_dict(metadata)
            if isinstance(metadata, dict)
            else EpubMetadata.from_novel(metadata)
            if isinstance(metadata, Novel)
            else metadata
        )
        self.extra_css = (
            extra_css if extra_css else metadata.extra_css if isinstance(metadata, Novel) else self.extra_css
        )
        self.options = EpubOptions.from_dict(options) if isinstance(options, dict) else options
        self.file_map = files or {}
        self.epub_uid = epub_uid or self.get_epub_uid()
        self.chapters = chapters or dict()
        self.image_map = dict()
        self.extra_css = extra_css
        self.cover_image_id = cover_image_id

        if not self.file_map:
            self.initialize()

    @property
    def epub_version(self) -> str:
        """Return the epub version string."""
        return self.options.epub_version

    def initialize(self):
        """Initialize the file list with the basic set of files that this package needs."""
        self.add_file(MimetypeFile())
        self.add_file(PyWebNovelJSON())
        self.add_file(ContainerXML())
        self.add_file(Stylesheet())
        self.add_file(NavigationControlFile())
        self.add_file(PackageOPF())
        self.add_file(NavXhtml())
        if self.include_title_page:
            self.add_file(TitlePage())
        if self.include_toc_page:
            self.add_file(TableOfContentsPage())

    @property
    def app_json(self) -> Optional[PyWebNovelJSON]:
        """Return the PyWebNovelJSON file if one exists."""
        return self.file_map.get(PyWebNovelJSON.file_id)

    @property
    def title_page(self) -> Optional[TitlePage]:
        """Return the TitlePage if one exists."""
        return self.file_map.get(TitlePage.file_id)

    @property
    def toc_page(self) -> Optional[TableOfContentsPage]:
        """Return the TableOfContentsPage if one exists."""
        return self.file_map.get(TableOfContentsPage.file_id)

    @property
    def mimetype_file(self) -> Optional[MimetypeFile]:
        """Return a MimetypeFile if one exists."""
        return self.file_map.get(MimetypeFile.file_id)

    @property
    def container_xml(self) -> Optional[ContainerXML]:
        """Return a ContainerXML if one exists."""
        return self.file_map.get(ContainerXML.file_id)

    @property
    def stylesheet(self) -> Optional[Stylesheet]:
        """Return a Stylesheet if one exists."""
        return self.file_map.get(Stylesheet.file_id)

    @property
    def ncx(self) -> Optional[NavigationControlFile]:
        """Return the NavigationControlFile if one exists."""
        return self.file_map.get(NavigationControlFile.file_id)

    @property
    def opf(self) -> Optional[PackageOPF]:
        """Return the PackageOPF file if one exists."""
        return self.file_map.get(PackageOPF.file_id)

    @property
    def nav(self) -> Optional[NavXhtml]:
        """Return the Nav XHTML file if one exists."""
        return self.file_map.get(NavXhtml.file_id)

    def add_file(self, file: EpubInternalFile) -> None:
        """Add a file to the package."""
        if file.file_id in self.file_map:
            logger.warning("overwriting file_id=%s", file.file_id)
        self.file_map[file.file_id] = file

    @property
    def images(self) -> list[ImageFile]:
        """Return a list of all the ImageFiles in this package (ordered by file path)."""
        return sorted(
            [epub_file for epub_file in self.file_map.values() if isinstance(epub_file, ImageFile)],
            key=lambda img: img.filename,
        )

    def add_image(self, image: Image, content: bytes, file_id: str = None, is_cover_image: bool = False) -> None:
        """
        Add an Image to the package.

        :param image: The Image.
        :param content: The contents of the image file.
        :param file_id: (optional) Manually override the file_id of the image file. Defaults to the SHA256 hash of the image contents.
        :param is_cover_image: (optional) A boolean that controls whether or not this image is the cover image of the epub.
        """
        if not self.include_images:
            logger.warning("Ignoring image. include_images is False.")
            return
        image_hash = hashlib.sha256(content).hexdigest()
        image_file = ImageFile(
            file_id=file_id or image_hash,
            mimetype=image.mimetype,
            extension=image.extension,
            is_cover_image=is_cover_image,
        )
        self.image_map[image_file.file_id] = content
        if is_cover_image:
            self.metadata.cover_image_url = image.url
            self.metadata.cover_image_id = image_file.file_id
            if self.cover_image:
                self.cover_image.is_cover_image = False
            if not self.cover_page:
                self.add_file(CoverPage())
        self.add_file(image_file)

    def save(self):
        """Save the epub package."""
        with ZipFile(self.zipio, "w") as zfh:
            for epub_file in self.file_map.values():
                # print(f"Writing: {epub_file.filename}")
                epub_file.write(pkg=self, zipfile=zfh)

    @property
    def cover_page(self) -> Optional[CoverPage]:
        """Return the cover page if one exists."""
        return self.file_map.get(CoverPage.file_id)

    @property
    def cover_image(self) -> Optional[ImageFile]:
        """Return the ImageFile for the cover image, if there is one."""
        return self.file_map.get(self.metadata.cover_image_id) if self.metadata.cover_image_id else None

    @classmethod
    def load(cls, filename: str, ignore_extra_data: bool = True) -> "EpubPackage":
        """
        Load an EpubPackage from an existing epub file.

        Note: this requires a valid PyWebNovelJSON file is in the epub package.

        :param filename: The filename of an epub file to load.
        :param ignore_extra_data: If there is extra information in the app .json file, ignore it.
        """
        expected_keys = {"options", "files", "metadata", "epub_uid", "chapters", "extra_css", "cover_image_id"}
        with open(filename, "rb") as fh:
            with ZipFile(fh, mode="r") as zfh:
                data = PyWebNovelJSON.load_from_pkg(zfh)
                keys = set(data.keys())
                unexpected_keys = keys - expected_keys
                if unexpected_keys and not ignore_extra_data:
                    raise ValueError(f"Encountered unexpected keys in epub json file: {unexpected_keys}")
                file_map = {
                    file_id: from_dict_to_file(file_dict) for file_id, file_dict in data.pop("files", {}).items()
                }
                chapters = {
                    chapter_id: Chapter.from_dict(chapter_data)
                    for chapter_id, chapter_data in data.pop("chapters", {}).items()
                }
                image_map = {}

                for file_id, epub_file in file_map.items():
                    if epub_file.mimetype.startswith("image/"):
                        image_map[file_id] = zfh.read(epub_file.filename)

        pkg = EpubPackage(**filter_dict(data, expected_keys), files=file_map, chapters=chapters, file_or_io=filename)
        pkg.image_map = image_map
        return pkg

    @property
    def include_toc_page(self) -> bool:
        """Return the include_toc_page option."""
        return self.options.include_toc_page

    @property
    def include_title_page(self) -> bool:
        """Return the include_title_page option."""
        return self.options.include_title_page

    @property
    def include_images(self) -> bool:
        """Return the include_images option."""
        return self.options.include_images

    @property
    def chapter_files(self) -> list[ChapterFile]:
        """Return a sorted list of all of the ChapterFiles in the epub."""
        return sorted(
            [epub_file for _, epub_file in self.file_map.items() if isinstance(epub_file, ChapterFile)],
            key=lambda chfile: chfile.file_id,
        )

    def add_chapter(self, chapter: Chapter, file_id: str = None) -> None:
        """Add a Chapter to the epub file."""
        chapter_count = len(self.chapters)
        chapter_no = chapter_count + 1
        chapter_file = ChapterFile(
            chapter_id=chapter.chapter_id,
            file_id=file_id or f"ch{chapter_no:05d}",
            title=chapter.title,
        )
        self.chapters[chapter.chapter_id] = chapter
        self.add_file(chapter_file)

    @property
    def is_epub3(self) -> bool:
        """Return a boolean indicating if this package is Epub version 3.x or not."""
        major_version, _, _ = str(self.epub_version).partition(".")
        return int(major_version) == 3

    def get_epub_uid(self):
        """Return a unique URN representing this package."""
        return f"urn:pywebnovel:uid:{self.metadata.site_id}:{self.metadata.novel_id}"
