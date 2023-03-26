"""Class representing the EPUB file."""

from dataclasses import dataclass
from inspect import isclass
from typing import IO, Optional, Union
from zipfile import ZIP_STORED, ZipFile

from apptk.http import HttpClient

from webnovel.data import Chapter, Image, Novel, NovelOptions
from webnovel.epub.files import (
    ChapterFile,
    ContainerXML,
    CoverPage,
    EpubFileInterface,
    EpubImage,
    MimetypeFile,
    NavigationControlFile,
    NavXhtml,
    PackageOPF,
    PyWebNovelJSON,
    Stylesheet,
    TableOfContentsPage,
    TitlePage,
)

from ..utils import normalize_io


class EpubFileList:
    """The file list of the contents of the epub file."""

    files: dict
    image_id_counter: int
    chapter_id_counter: int
    cover_image_id: Optional[str] = None
    cover_image: Optional[EpubImage] = None

    def __init__(self):
        self.image_id_counter = 0
        self.chapter_id_counter = 0
        self.files = {}

    def has_file(self, key) -> bool:
        """
        Test of a file represented by key is in the file list.

        Various methods are used.
        """
        # if key is a string, handle it as a file_id
        if isinstance(key, str):
            return key in self

        # if it's a class, then we assume we're testing if an instance of this
        # class is a file in the list. For example, has_file(CoverImage) would
        # be checking if there is a cover image defined.
        if isclass(key):
            return any(isinstance(epub_file, key) for epub_file in self.files.values())

        # otherwise, we fall back on assuming that key is an file instance that we're
        # checking for.
        return any(key == epub_file or key is epub_file for epub_file in self.files.values())

    def generate_image_id(self):
        """Generate a new, unused file_id for an image."""
        image_id = None
        while image_id is None or image_id in self:
            image_id = f"image{self.image_id_counter:03d}"
            self.image_id_counter += 1
        return image_id

    def add_image(self, image: Union[EpubImage, Image], is_cover_image: bool = False, client: HttpClient = None) -> str:
        """Add an image to the file list."""
        if isinstance(image, Image):
            image.load(client=client)
            image = EpubImage.from_image(image=image, image_id=self.generate_image_id())
        assert isinstance(image, EpubImage), "add_image can only handle Image or EpubImage instances."
        self.files[image.file_id] = image

        if is_cover_image:
            self.cover_image_id = image.file_id
            self.cover_image = image

        return image.file_id

    def generate_chapter_id(self) -> str:
        """Generate a new, unused file_id for an chapter."""
        chapter_id = None
        while chapter_id is None or chapter_id in self:
            chapter_id = f"ch{self.chapter_id_counter:05d}"
            self.chapter_id_counter += 1
        return chapter_id

    def add_chapter(self, chapter: Chapter, pkg: "EpubPackage") -> str:
        """Create a ChapterFile from Chapter and add to the file list."""
        file_id = self.generate_chapter_id()
        chap_file = ChapterFile(pkg=pkg, chapter=chapter, file_id=file_id)
        self.files[file_id] = chap_file
        return file_id

    def add(self, epub_file: EpubFileInterface) -> str:
        """Add a file to the list."""
        if isinstance(epub_file, (Image, EpubImage)):
            return self.add_image(epub_file)
        if not epub_file.file_id:
            raise ValueError(f"EpubFile.file_id is None: epub_file={epub_file!r}")
        self.files[epub_file.file_id] = epub_file
        return epub_file.file_id

    @property
    def images(self):
        """Return a list of all images in the file list."""
        return [item for _, item in self.files.items() if isinstance(item, EpubImage)]

    @property
    def chapters(self):
        """Return a list of all of the chapter files."""
        return sorted([item for item in self.files.values() if isinstance(item, ChapterFile)], key=lambda i: i.file_id)

    def __iter__(self):
        """Return an iterator over all files in the list."""
        return iter(self.files.values())

    def __getitem__(self, key):
        """Allow lookups into the file list by file_id."""
        if key in self.files:
            return self.files[key]
        raise KeyError(f"No file with file_id={key!r} in list.")

    def __contains__(self, key):
        """Test of file_id is in the file list."""
        return key in self.files

    def generate_toc_list(self) -> list:
        """Generate the list of items to include in the TOC."""
        toc_files = []
        if self.cover_page:
            toc_files.append(self.cover_page)
        if self.title_page:
            toc_files.append(self.title_page)
        if self.toc_page:
            toc_files.append(self.toc_page)
        toc_files += sorted(self.chapters, key=lambda ch: ch.file_id)
        return toc_files

    def generate_spine_items(self) -> list:
        """Generate the list of items to include in the <spine>."""
        items = []
        if self.cover_page:
            items.append(self.cover_page)
        if self.title_page:
            items.append(self.title_page)
        if self.toc_page:
            items.append(self.toc_page)
        items.extend(self.chapters)
        return items

    @property
    def has_toc_page(self) -> bool:
        """Test if a table of contents page is in the list."""
        return "toc_page" in self

    @property
    def toc_page(self) -> Optional[TableOfContentsPage]:
        """Return the table of contents page, if it exists."""
        file_id = TableOfContentsPage.file_id
        return self[file_id] if file_id in self else None

    @property
    def has_cover_page(self) -> bool:
        """Test if the cover page is included in the file list."""
        return self.cover_page is not None

    @property
    def cover_page(self) -> Optional[CoverPage]:
        """Return the cover page, if one exists."""
        file_id = CoverPage.file_id
        return self[file_id] if file_id in self else None

    @property
    def title_page(self) -> Optional[TitlePage]:
        """Return the title page, if one exists."""
        file_id = TitlePage.file_id
        return self[file_id] if file_id in self else None


@dataclass
class NovelInfo:
    """Summarized Novel Information."""

    title: str
    site_id: str
    novel_id: str
    novel_url: str
    novel_metadata: dict
    cover_image_url: Optional[str] = None

    @classmethod
    def from_novel(cls, novel: Novel) -> "NovelInfo":
        """Create instance from a Novel instance."""
        return cls(
            title=novel.title,
            site_id=novel.site_id,
            novel_id=novel.novel_id,
            novel_url=novel.url,
            cover_image_url=novel.cover_image.url if novel.cover_image else None,
            novel_metadata={
                "author": novel.author.to_dict() if novel.author else None,
                "translator": novel.translator.to_dict() if novel.translator else None,
                "status": novel.status,
                "genres": novel.genres,
                "tags": novel.tags,
            },
        )


class EpubPackage:
    """A representation of an epub ebook file."""

    filename: str
    novel: Novel
    novel_info: NovelInfo
    epub_version: str
    pkg_opf_path: str
    default_language_code: str
    files: EpubFileList

    def __init__(
        self,
        filename: str,
        novel: Novel,
        options: NovelOptions,
        default_language_code: str = "en",
        version: str = "3.0",
        pkg_opf_path: str = "package.opf",
    ) -> None:
        self.filename = filename
        self.novel = novel
        self.options = options
        self.novel_info = NovelInfo.from_novel(novel)
        self.default_language_code = default_language_code
        self.epub_version = version
        self.pkg_opf_path = pkg_opf_path
        self.files = self.build_file_list()

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

    def build_file_list(self) -> EpubFileList:
        """Generate the initial file list for the epub package."""
        files = EpubFileList()
        files.add(MimetypeFile(self))
        files.add(ContainerXML(self))
        files.add(PackageOPF(self))
        files.add(NavigationControlFile(self))
        files.add(NavXhtml(self))
        files.add(Stylesheet(self))

        if self.include_title_page:
            files.add(TitlePage(self))

        if self.include_toc_page:
            files.add(TableOfContentsPage(self))

        files.add(PyWebNovelJSON(self))
        return files

    def add_image(
        self, image: Union[Image, EpubImage], is_cover_image: bool = False, client: HttpClient = None
    ) -> None:
        """
        Add an image to the package.

        If the image is a cover image, add the cover page to display it.
        """
        self.files.add_image(image, is_cover_image=is_cover_image, client=client)
        if is_cover_image and not self.files.has_cover_page:
            self.files.add(CoverPage(self))

    def add_chapter(self, chapter) -> None:
        """Add a Chapter to the epub file."""
        self.files.add_chapter(chapter, self)

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
    def cover_image(self) -> Optional[EpubImage]:
        """Return the cover image file."""
        return self.files.cover_image

    def save(self, file_or_io: Union[str, IO]) -> IO:
        """
        Save the Epub to a file.

        :param file_or_io: A IO instance or a filename/filepath string.
        """
        zipio = normalize_io(file_or_io, "wb")
        zipfile = ZipFile(zipio, "w", compression=ZIP_STORED)

        for pkg_file in self.files:
            # If images are turned off, don't include images or the cover page.
            if not self.include_images and isinstance(pkg_file, (CoverPage, EpubImage)):
                continue

            # If the file's content is blank, run generate() to fill it in.
            if pkg_file.data is None:
                pkg_file.generate()

            zipfile.writestr(pkg_file.filename, pkg_file.data)
        zipfile.close()
        return zipio
