from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from webnovel.epub.pkg import EpubPackage


class BasicFileInterface:
    filename: str
    data: bytes = None
    pkg: "EpubPackage" = None


class EpubFileInterface(BasicFileInterface):
    file_id: str
    filename: str
    mimetype: str
    title: str = None
    include_in_spine: bool = False
    data: bytes = None
    pkg: "EpubPackage" = None


@dataclass
class EpubFile(EpubFileInterface):
    file_id: str
    filename: str
    mimetype: str
    title: str = None
    include_in_spine: bool = False
    data: bytes = None
    pkg: "EpubPackage" = None
