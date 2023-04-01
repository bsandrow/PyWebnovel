"""Representations of scraper data to be stored within the EPUB file."""

from dataclasses import asdict, dataclass, fields
from enum import Enum
from typing import TYPE_CHECKING, Optional

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
    title: Optional[str] = None
    status: Optional[NovelStatus] = NovelStatus.UNKNOWN
    summary: Optional[str] = None
    summary_type: SummaryType = SummaryType.text
    genres: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    author: Optional[Person] = None
    translator: Optional[Person] = None
    cover_image_url: Optional[str] = None
    cover_image_id: Optional[str] = None
    extras: Optional[dict] = None

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
        return EpubMetadata(**kwargs)

    def to_dict(self) -> dict:
        """Convert EpubMetadata to a dict."""
        field_names = tuple(field.name for field in fields(self.__class__))
        data = {name: getattr(self, name, None) for name in field_names}
        data["author"] = self.author.to_dict() if self.author else None
        data["translator"] = self.translator.to_dict() if self.translator else None
        data["status"] = self.status.value if self.status else None
        data["summary_type"] = self.summary_type.value
        return data
