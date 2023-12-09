"""Representations of scraper data to be stored within the EPUB file."""

from dataclasses import asdict, dataclass, field, fields
import datetime
from enum import Enum
import functools
import logging
from typing import TYPE_CHECKING, Any, Callable

from bs4 import Tag

from webnovel import errors
from webnovel.data import Chapter, Novel, NovelStatus, Person
from webnovel.utils import DataclassSerializationMixin, filter_dict

if TYPE_CHECKING:
    from webnovel.epub.pkg import NovelInfo


logger = logging.getLogger(__name__)


class SummaryType(Enum):
    """Indicate whether the summary string is text or html."""

    html = "html"
    text = "text"


class MetadataVersion(Enum):
    """The version of the metadata format."""

    v1 = 1
    v2 = 2


@dataclass
class EpubOptions(DataclassSerializationMixin):
    """Collection of settings for the novel."""

    include_toc_page: bool = True
    include_title_page: bool = True
    include_images: bool = True
    epub_version: str = "3.0"


@dataclass
class ChangeLogEntry(DataclassSerializationMixin):
    """An entry in the ChangeLog."""

    message: str
    created: datetime.datetime = field(default_factory=lambda: datetime.datetime.utcnow())
    new_value: Any | None = None
    old_value: Any | None = None


@dataclass
class ChangeLog:
    """A ChangeLog that records changes to the epub file."""

    entries: list[ChangeLogEntry] = field(default_factory=list)
    last_updated: datetime.datetime | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "ChangeLog":
        """Load from dictionary."""
        entries = data.pop("entries")
        last_updated = data.pop("last_updated", None)
        if last_updated:
            last_updated = datetime.datetime.fromisoformat(last_updated)
        return cls(entries=entries, last_updated=last_updated)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "entries": [entry.to_dict() for entry in self.entries],
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


@dataclass
class EpubMetadata:
    """Representation of the scraper.json file stored in .epub file."""

    novel_url: str
    novel_id: str
    site_id: str
    title: str | None = None
    status: NovelStatus | None = NovelStatus.UNKNOWN
    summary: str | None = None
    summary_type: SummaryType = SummaryType.text
    genres: list[str] | None = None
    tags: list[str] | None = None
    author: Person | None = None
    translator: Person | None = None
    cover_image_url: str | None = None
    cover_image_id: str | None = None
    published_on: datetime.date | None = None
    last_updated_on: datetime.date | None = None
    extras: dict | None = None
    change_log: list[ChangeLog] | None = field(default_factory=ChangeLog)

    #: The version of the metadata. This is necessary to allow changes to
    #: metadata structure while allowing handling of epubs created with previous
    #: metadata formats.
    version: MetadataVersion = field(default_factory=lambda: EpubMetadata.CURRENT_VERSION)

    #: The current "default" version of the metadata.  This is used as the
    #: default version when creating new metadata, and also as the target
    #: version (for conversion) when loading older versions of the metadata.
    CURRENT_VERSION: MetadataVersion = MetadataVersion.v2

    #: A mapping that maps a version of the metadata to the method that will be
    #: used to convert it to the next metadata version above it.  For example::
    #:
    #:    {v1: "convert_to_v2"}
    #:
    #: Would call convert_to_v2 to convert metadata from v1 format to v2 format.
    VERSION_CONVERSION_MAP = {}

    @staticmethod
    def detect_version(data: dict) -> MetadataVersion:
        """
        Extract the version (as a MetadataVersion) from data.

        Version could either be a string or an int, but ultimately should be
        convertible to an integer (and mapped to a version in the enum).

        ..note:
            "version" didn't exist in v1, so if it's missing assume that this is
            metadata v1.
        """
        version_raw = data.get("version", "1")
        try:
            return MetadataVersion(int(version_raw))
        except ValueError:
            raise errors.EpubParseError(f"Bad version value in epub metadata: {version_raw}")

    @classmethod
    def build_conversion_path(cls, data: dict, target_version: MetadataVersion) -> list[Callable]:
        """
        Build a sequence of functions to convert data to target_version.

        :params data: Raw metadata
        :params target_version: The metadata version to convert to.
        """
        assert isinstance(target_version, MetadataVersion)
        conversion_path = []
        current_version = cls.detect_version(data)
        logger.debug("Building conversion path from %s to %s", current_version.name, target_version.name)

        while current_version.value < target_version.value:
            next_version = MetadataVersion(current_version.value + 1)
            conversion_func = cls.VERSION_CONVERSION_MAP.get(current_version)
            logger.debug("Fetching conversion function (%s -> %s).", current_version.name, next_version.name)

            if not conversion_func:
                raise errors.EpubError("No function to convert from {current_version} to {next_version}")
            current_version = next_version
            conversion_path.append(conversion_func)

        return conversion_path

    @classmethod
    def convert_to_version(cls, data: dict, target_version: MetadataVersion) -> dict:
        """
        Convert raw metadata into target version.

        :params data: Raw metadata
        :params target_version: The version to convert the metadata into
        """
        return functools.reduce(lambda d, f: f(d), cls.build_conversion_path(data, target_version), data)

    @classmethod
    def convert_to_current_version(cls, data: dict) -> dict:
        """
        Convert raw metadata into the default version.

        :params data: Raw metadata
        """
        return cls.convert_to_version(data, cls.CURRENT_VERSION)

    @classmethod
    def from_novel(cls, novel: Novel) -> "EpubMetadata":
        """Create EpubMetadata from a Novel instance."""
        return EpubMetadata(
            novel_url=novel.url,
            novel_id=novel.novel_id,
            site_id=novel.site_id,
            title=novel.title,
            status=novel.status,
            genres=novel.genres,
            tags=novel.tags,
            author=novel.author,
            translator=novel.translator,
            summary=str(novel.summary) if novel.summary else None,
            summary_type=SummaryType.html if isinstance(novel.summary, Tag) else SummaryType.text,
            cover_image_url=novel.cover_image.url if novel.cover_image else None,
            published_on=novel.published_on,
            last_updated_on=novel.last_updated_on,
            extras=novel.extras,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "EpubMetadata":
        """Load EpubMetadata from a dict."""
        field_names = tuple(field.name for field in fields(cls))
        kwargs = filter_dict(data, field_names)
        kwargs["author"] = Person.from_dict(data["author"]) if data.get("author") else None
        kwargs["translator"] = Person.from_dict(data["translator"]) if data.get("translator") else None
        kwargs["status"] = NovelStatus(data["status"]) if data.get("status") else NovelStatus.UNKNOWN
        kwargs["summary_type"] = SummaryType(data["summary_type"]) if data.get("summary_type") else SummaryType.text
        kwargs["published_on"] = (
            datetime.datetime.strptime(kwargs["published_on"], "%Y-%m-%d") if kwargs.get("published_on") else None
        )
        kwargs["last_updated_on"] = (
            datetime.datetime.strptime(kwargs["last_updated_on"], "%Y-%m-%d") if kwargs.get("last_updated_on") else None
        )
        kwargs["change_log"] = ChangeLog.from_dict(data["change_log"]) if data.get("change_log") else None
        return EpubMetadata(**kwargs)

    def to_dict(self) -> dict:
        """Convert EpubMetadata to a dict."""
        field_names = tuple(field.name for field in fields(self.__class__))
        data = {name: getattr(self, name, None) for name in field_names}
        data["author"] = self.author.to_dict() if self.author else None
        data["translator"] = self.translator.to_dict() if self.translator else None
        data["status"] = self.status.value if self.status else None
        data["summary_type"] = self.summary_type.value
        data["published_on"] = self.published_on.strftime("%Y-%m-%d") if self.published_on else None
        data["last_updated_on"] = self.last_updated_on.strftime("%Y-%m-%d") if self.last_updated_on else None
        data["change_log"] = self.change_log.to_dict() if self.change_log else None
        return data
