"""Define all of the basic datastructures we'll use to pass novels around."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class NovelStatus(Enum):
    ONGOING = "On Going"
    HIATUS = "Hiatus"
    DROPPED = "Dropped"
    COMPLETED = "Completed"
    UNKNOWN = "Unknown"


@dataclass
class Person:
    name: str
    email: str = None
    url: str = None


@dataclass
class Chapter:
    url: str
    title: str = None
    chapter_no: str = None


@dataclass
class Novel:
    url: str
    title: str = None
    status: NovelStatus = None
    summary: str = None
    genres: list[str] = None
    tags: list[str] = None
    author: Optional[Person] = None
    translator: Person = None
    chapters: list[Chapter] = None
