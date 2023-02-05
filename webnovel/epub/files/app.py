"""Files in the .epub Package that are internal to PyWebnovel."""

from typing import TYPE_CHECKING

from webnovel.epub.files import EpubFileInterface

if TYPE_CHECKING:
    from webnovel.epub.pkg import EpubPackage


class PyWebNovelJSON(EpubFileInterface):
    file_id: str = "pywebnovel-meta"
    filename: str = "pywebnovel.json"
    mimetype: str = "application/json"
    title: str = None
    include_in_spine: bool = False
    data: bytes = None
    pkg: "EpubPackage" = None

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg
