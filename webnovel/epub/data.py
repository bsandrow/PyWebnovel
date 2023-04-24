"""Representations of scraper data to be stored within the EPUB file."""

from dataclasses import asdict, dataclass, fields
import datetime
from enum import Enum
from typing import TYPE_CHECKING

from bs4 import Tag

from webnovel.data import Chapter, Novel, NovelStatus, Person
from webnovel.utils import filter_dict

if TYPE_CHECKING:
    from webnovel.epub.pkg import NovelInfo


class SummaryType(Enum):
    """Indicate whether the summary string is text or html."""

    html = "html"
    text = "text"


@dataclass
class EpubOptions:
    """Collection of settings for the novel."""

    include_toc_page: bool = True
    include_title_page: bool = True
    include_images: bool = True
    epub_version: str = "3.0"

    @classmethod
    def from_dict(cls, data: dict) -> "EpubOptions":
        """Load EpubOptions from a dict."""
        field_names = tuple(field.name for field in fields(cls))
        return EpubOptions(**{key: value for key, value in data.items() if key in field_names})

    def to_dict(self) -> dict:
        """Convert EpubOptions to a dict."""
        return asdict(self)


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
        return data
