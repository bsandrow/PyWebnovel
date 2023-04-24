"""New Data Model."""

from collections import namedtuple
from dataclasses import InitVar, dataclass, field
import datetime
import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from webnovel.data import Chapter
    from webnovel.epub.files import EpubInternalFile


ChangedValue = namedtuple("ChangedValue", ["field", "old", "new"])


class ChangeType(enum.Enum):
    """The type of change that a particular log entry is recording."""

    CREATED = 1
    SET_COVER = 2
    CHANGE = 3


ENTRY_MESSAGES = {
    ChangeType.CREATED: "Ebook Created.",
    ChangeType.SET_COVER: "Ebook Cover Changed.",
}


@dataclass
class ChangeLog:
    """A log of all changes made to the ebook since creation."""

    entries: list["ChangeLogEntry"] = field(default_factory=list)

    def initialize_log(self):
        """Initialize the changelog with an initial creation log entry."""
        if not self.entries:
            self.entries.append(ChangeLogEntry.build_initial_log_entry())

    def log_cover_change(self, oldurl: str, newurl: str, oldid: str, newid: str):
        """
        Log a cover image change to the ebook.

        :param oldurl: The previous value of cover_image_url.
        :param newurl: The new value of cover_image_url.
        :param oldid: The previous value of cover_image_id.
        :param newid: The new value of cover_image_id.
        """
        self.entries.append(ChangeLogEntry.build_set_cover_entry(oldurl, newurl, oldid, newid))

    def to_dict(self) -> dict:
        """Convert to a dictionary."""
        return {"entries": [entry.to_dict() for entry in self.entries]}

    @classmethod
    def from_dict(cls, input: dict) -> "ChangeLog":
        """Load a ChangeLog from a dictionary."""
        return cls(entries=[ChangeLogEntry.from_dict(d) for d in input["entries"]])


@dataclass
class ChangeLogEntry:
    """An entry in the ChangeLog."""

    type: ChangeType
    timestamp: datetime.datetime = field(default_factory=lambda: datetime.datetime.utcnow())
    changes: list[ChangedValue] = field(default_factory=list)

    @classmethod
    def build_initial_log_entry(cls) -> "ChangeLogEntry":
        """Build a ChangeLogEntry for initial ebook creation."""
        return ChangeLogEntry(type=ChangeType.CREATED)

    @classmethod
    def build_set_cover_entry(cls, oldurl: str, newurl: str, oldid: str, newid: str) -> "ChangeLogEntry":
        """Build a ChangeLogEntry for setting the cover image of the ebook."""
        entry = cls(type=ChangeType.SET_COVER)
        entry.changes.append(ChangedValue("metadata.cover_image_url", oldurl, newurl))
        entry.changes.append(ChangedValue("metadata.cover_image_id", oldid, newid))
        return entry

    def to_dict(self) -> dict:
        """Serialize into a dictionary."""
        return {
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "changes": [(change.field, change.old, change.new) for change in self.changes],
        }

    @classmethod
    def from_dict(cls, input: dict) -> "ChangeLogEntry":
        """Create a ChangeLogEntry from a dictionary."""
        incoming_keys = set(input.keys())
        valid_keys = required_keys = {"type", "timestamp", "changes"}

        missing_keys = required_keys - incoming_keys
        if missing_keys:
            keys = ", ".join(map(repr, missing_keys))
            raise ValueError(f"Missing require keys ({keys}) from ChangeLogEntry: dict={input!r}.")

        nonvalid_keys = incoming_keys - valid_keys
        if nonvalid_keys:
            keys = ", ".join(map(repr, nonvalid_keys))
            raise ValueError(f"Found the following non-valid keys ({keys}) in input={input!r}")

        assert input["type"] is not None
        assert input["timestamp"] is not None
        assert input["changes"] is not None

        return cls(
            type=ChangeType[int(input["type"])],
            timestamp=datetime.datetime.fromisoformat(input["timestamp"]),
            changes=[ChangedValue(*change) for change in input["changes"]],
        )


class NovelMetadata:
    """Novel metadata."""


class PackageOptions:
    """Options Related to the Generation of the Ebook format."""

    # Control whether or not to add a Table of Contents page in the package.
    include_toc_page: bool = True

    # Control whether or not to add a title page to the ebook.
    include_title_page: bool = True

    # Control whether or not to embed images in the ebook.
    include_images: bool = True

    # Control which epub version to use when generating the ebook. In the
    # future, if more formats are included, this will probably just be ignored
    # by those formats
    epub_version: str = "3.0"

    # Additional CSS to add to the ebook. Note: This will only be respected for
    # ebook formats that use HTML.
    extra_css: str | None = None


class EbookData:
    """New Data Model."""

    ebook_uid: str
    metadata: NovelMetadata
    options: PackageOptions = field(default_factory=PackageOptions)
    chapters: dict[str, "Chapter"] = field(default_factory=dict)
    files: dict[str, "EpubInternalFile"] = field(default_factory=dict)
    changelog: ChangeLog = field(default_factory=ChangeLog)

    # backwards compatibility
    extra_css: InitVar[str | None]
    epub_uid: InitVar[str | None]

    def __post_init__(self, extra_css: str | None, epub_uid: str | None) -> None:
        """Allow extra_css / epub_uid as init options stick them in their new locations."""
        if self.ebook_uid is None and epub_uid is not None:
            self.ebook_uid = epub_uid
        if self.options.extra_css is None and extra_css is not None:
            self.options.extra_css = extra_css

    @property
    def extra_css(self) -> str | None:
        """Return extra_css from its new location for backwards-compatibility."""
        return self.options.extra_css

    @property
    def epub_uid(self) -> str:
        """Return ebook_uid as epub_uid for backwards-compatibility."""
        return self.ebook_uid
