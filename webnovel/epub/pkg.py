"""Class representing the EPUB file."""

from inspect import isclass
from typing import IO, Union
from zipfile import ZIP_STORED, ZipFile

from apptk.func import cached_property

from webnovel.data import Image
from webnovel.epub.files import (  # TableOfContentsPage,
    ContainerXML,
    CoverPage,
    EpubFileInterface,
    EpubImage,
    MimetypeFile,
    NavigationControlFile,
    PyWebNovelJSON,
    Stylesheet,
    TitlePage,
)

from ..utils import normalize_io
from .data import EpubNovel


class EpubFileList:
    """The file list of the contents of the epub file."""

    files: dict = None
    image_id_counter: int = None
    cover_image_id: str = None
    cover_image: EpubImage = None

    def __init__(self):
        self.image_id_counter = 0
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

    def add_image(self, image: Union[EpubImage, Image], is_cover_image: bool = False) -> str:
        """Add an image to the file list."""
        if isinstance(image, Image):
            image.load()
            image = EpubImage.from_image(image=image, image_id=self.generate_image_id())
        assert isinstance(image, EpubImage), "add_image can only handle Image or EpubImage instances."
        self.files[image.file_id] = image

        if is_cover_image:
            self.cover_image_id = image.file_id
            self.cover_image = image

        return image.file_id

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

    # @property
    # def chapters(self):
    #     return []
    #     # return [item for _, item in self.files.items() if isinstance(item, EpubChapter)]

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

    @property
    def has_toc_page(self) -> bool:
        """Test if a table of contents page is in the list."""
        return "toc_page" in self

    @property
    def has_cover_page(self) -> bool:
        """Test if the cover page is included in the file list."""
        return CoverPage.file_id in self


class EpubPackage:
    """A representation of an epub ebook file."""

    filename: str
    novel: EpubNovel
    epub_version: str
    pkg_opf_path: str
    include_toc_page: bool
    include_title_page: bool
    default_language_code: str
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
        self.default_language_code = default_language_code
        self.epub_version = version
        self.pkg_opf_path = pkg_opf_path
        self.include_toc_page = include_toc_page
        self.include_title_page = include_title_page
        self.include_images = include_images
        self.files = self.build_file_list()

    def build_file_list(self) -> EpubFileList:
        """Generate the initial file list for the epub package."""
        files = EpubFileList()
        files.add(MimetypeFile(self))
        files.add(ContainerXML(self))
        files.add(NavigationControlFile(self))
        files.add(Stylesheet(self))

        if self.include_title_page:
            files.add(TitlePage(self))

        # if self.include_toc_page:
        #     files.add(TableOfContentsPage(self))

        files.add(PyWebNovelJSON(self))
        return files

    def add_image(self, image: Union[Image, EpubImage], is_cover_image: bool = False) -> None:
        """
        Add an image to the package.

        If the image is a cover image, add the cover page to display it.
        """
        self.files.add_image(image, is_cover_image=is_cover_image)
        if is_cover_image and not self.files.has_cover_page:
            self.files.add(CoverPage(self))

    # def add_chapter(self, chapter) -> None:
    #     self.files.add(chapter)
    #     if self.include_title_page:
    #         self.files.add(TableOfContentsPage(self))

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
