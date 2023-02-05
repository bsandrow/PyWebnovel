"""Class representing the EPUB file."""

from typing import IO, Union
from zipfile import ZipFile, ZIP_STORED

from apptk.func import cached_property

from .data import EpubNovel
from ..utils import normalize_io

from webnovel.epub.files import (
    EpubFileInterface,
    EpubImages,
    EpubImage,
    TableOfContentsPage,
    MimetypeFile,
    ContainerXML,
    PyWebNovelJSON,
    NavigationControlFile,
    TitlePage,
    Stylesheet,
)


class EpubFileList:
    files: dict = None

    def __init__(self):
        self.files = {}

    def add(self, epub_file: EpubFileInterface) -> None:
        if not epub_file.file_id:
            raise ValueError(f"EpubFile.file_id is None: epub_file={epub_file!r}")
        self.files[epub_file.file_id] = epub_file

    @property
    def images(self):
        return [item for _, item in self.files.items() if isinstance(item, EpubImage)]

    @property
    def chapters(self):
        return []
        # return [item for _, item in self.files.items() if isinstance(item, EpubChapter)]

    def __iter__(self):
        return iter(self.files.values())

    def __getitem__(self, key):
        if key in self.files:
            return self.files[key]
        raise KeyError(f"No file with file_id={key!r} in list.")

    def __contains__(self, key):
        return key in self.files

    @property
    def has_toc_page(self):
        return "toc_page" in self


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
    stylesheet_path: str = "stylesheet.css"  # TODO connect this with file
    files: EpubFileList = None

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
        self.files = self.build_file_list()

    def build_file_list(self) -> EpubFileList:
        files = EpubFileList()
        # files.add(MimetypeFile(self))
        # files.add(ContainerXML(self))
        files.add(PyWebNovelJSON(self))
        files.add(NavigationControlFile(self))
        files.add(Stylesheet(self))
        if self.include_title_page:
            files.add(TitlePage(self))
        if self.include_toc_page:
            files.add(TableOfContentsPage(self))
        return files

    def add_chapter(self, chapter) -> None:
        self.files.add(chapter)
        if self.include_title_page:
            self.files.add(TableOfContentsPage(self))

    @property
    def is_epub3(self) -> bool:
        """Return a boolean indicating if this package is Epub version 3.x or not."""
        major_version, _, _ = str(self.epub_version).partition(".")
        return int(major_version) == 3

    @property
    def epub_uid(self):
        """Return a unique URN representing this package."""
        return f"urn:pywebnovel:uid:{self.novel.site_id}:{self.novel.novel_id}"

    @property
    def cover_image(self) -> EpubImage:
        """Return the cover image file."""
        return self.images[self.images.cover_image] if self.images.cover_image else None

    def save(self, file_or_io: Union[str, IO]) -> IO:
        zipio = normalize_io(file_or_io, "wb")
        zipfile = ZipFile(zipio, "w", compression=ZIP_STORED)
        for pkg_file in self.files:
            if pkg_file.data is None:
                pkg_file.generate(pkg=self)
            zipfile.writestr(pkg_file.filename, pkg_file.data)
        zipfile.close()
        return zipio
