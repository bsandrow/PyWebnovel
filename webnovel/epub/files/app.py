"""Files in the .epub Package that are internal to PyWebnovel."""

import json
from typing import TYPE_CHECKING

from webnovel.epub.files import EpubFileInterface

if TYPE_CHECKING:
    from webnovel.epub.pkg import EpubPackage


class PyWebNovelJSON(EpubFileInterface):
    """
    A JSON file storing information about the webnovel.

    This file is a place to store PyWebnovel specific information so that it can
    be read out of existing epub files to do things like (e.g.) fetch additional
    chapters and add them to the file.
    """

    file_id: str = "pywebnovel-meta"
    filename: str = "pywebnovel.json"
    mimetype: str = "application/json"
    title: str = None
    include_in_spine: bool = False
    data: bytes = None
    pkg: "EpubPackage" = None

    def __init__(self, pkg: "EpubPackage") -> None:
        self.pkg = pkg

    def generate(self) -> None:
        """Serialize the novel information into the data attribute as JSON."""
        data = {}
        self.data = json.dumps(data).encode("utf-8")
