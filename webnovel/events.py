"""Event-handling for PyWebnovel."""

import enum
import logging
from typing import Callable

from webnovel.utils import Namespace

logger = logging.getLogger(__name__)


class Event(enum.Enum):
    """An enum of all PyWebnovel events."""

    EBOOK_UPDATE_START = "ebook-update-start"
    EBOOK_CREATE_START = "ebook-create-start"
    EBOOK_CREATE_END = "ebook-create-end"
    SET_COVER_IMAGE = "set-cover-image"
    SCRAPE_TOTAL_CHAPTERS = "scrape-total-chapters"
    PROCESS_CHAPTER_BATCH_START = "process-chapter-batch-start"
    PROCESS_CHAPTER_BATCH_END = "process-chapter-batch-end"

    # ~ Generic Webnovel Events ~
    FETCHING_CHAPTERS_START = "fetching-chapters-start"
    FETCHING_CHAPTERS_END = "fetching-chapters-end"

    # ~ Webnovel Update Events ~
    WEBNOVEL_UPDATE_NO_NEW_CHAPTERS = "webnovel-update-no-new-chapters"
    WEBNOVEL_UPDATE_CHAPTER_COUNT = "webnovel-update-chapter-count"
    WEBNOVEL_UPDATE_NEW_CHAPTER_COUNT = "webnovel-update-new-chapter-count"

    # ~ Webnovel Directory Events ~
    WEBNOVEL_DIR_WEBNOVEL_ADDED = "webnovel-dir-webnovel-added"
    WEBNOVEL_DIR_NOVEL_UPDATE_START = "webnovel-dir-novel-update-start"
    WEBNOVEL_DIR_NOVEL_UPDATE_END = "webnovel-dir-novel-update-end"
    WEBNOVEL_DIR_UPDATE_START = "webnovel-dir-update-start"
    WEBNOVEL_DIR_UPDATE_END = "webnovel-dir-update-end"
    WEBNOVEL_DIR_SAVE_START = "webnovel-dir-save-start"
    WEBNOVEL_DIR_SAVE_END = "webnovel-dir-save-end"
    WEBNOVEL_DIR_SKIP_PAUSED_NOVEL = "webnovel-dir-skip-paused-novel"
    WEBNOVEL_DIR_SKIP_COMPLETE_NOVEL = "webnovel-dir-skip-complete-novel"


LOGGING_MAP = {
    Event.FETCHING_CHAPTERS_END: lambda ctx: (
        "Averaged %.2f second(s) per chapter or %.2f chapter(s) per second.",
        ctx.time_per_chapter,
        1.0 / ctx.time_per_chapter,
    ),
    Event.WEBNOVEL_UPDATE_NO_NEW_CHAPTERS: lambda ctx: ("%s: No New Chapters Found.", ctx.path.name),
    Event.WEBNOVEL_UPDATE_CHAPTER_COUNT: lambda ctx: ("%s: %d Chapter(s) Found.", ctx.path.name, ctx.total),
    Event.WEBNOVEL_UPDATE_NEW_CHAPTER_COUNT: lambda ctx: ("%s: %d New Chapter(s) Found.", ctx.path.name, ctx.new),
    Event.WEBNOVEL_DIR_SKIP_PAUSED_NOVEL: lambda ctx: ("Skipping paused webnovel: %s", ctx.novel.path.name),
    Event.WEBNOVEL_DIR_SKIP_COMPLETE_NOVEL: lambda ctx: ("Skipping completed webnovel: %s", ctx.novel.path.name),
    Event.WEBNOVEL_DIR_SAVE_START: lambda ctx: ("Saving webnovel directory status (%s).", ctx.dir.directory),
    Event.WEBNOVEL_DIR_WEBNOVEL_ADDED: lambda ctx: (
        "Webnovel %s added to directory (%s).",
        ctx.path.name,
        ctx.dir.directory,
    ),
    Event.PROCESS_CHAPTER_BATCH_START: lambda ctx: (
        "Processing chapters '%s' to '%s'. [%d chapter(s)]",
        ctx.batch[0].title,
        ctx.batch[-1].title,
        ctx.batch_size,
    ),
}


class Context(Namespace):
    """
    The context of a triggered event.

    Contains details that event handlers can use to handle said event.
    """

    event: Event | None = None


class EventRegistry:
    """The registry of callbacks to trigger whenever and event occurs."""

    _map: dict[Event, list[Callable]]

    def __init__(self):
        self._initialize_callback_map()

    def _initialize_callback_map(self):
        """Set all events to an empty list of callbacks."""
        self._map = {event: [] for event in Event}

    def clear(self):
        """Reset the current registry, removing all registered callbacks."""
        self._initialize_callback_map()

    def register(self, event: Event, callback: Callable[[Context], None]) -> None:
        """Register a callback to handle the specified event."""
        self._map[event].append(callback)

    def trigger(self, event: Event, context: dict, logger: logging.Logger = logger) -> None:
        """Trigger the specified event, running all callbacks."""
        context = Context(context)
        context.event = event

        if event in LOGGING_MAP:
            args = LOGGING_MAP[event](context)
            logger.debug(*args)

        for callback in self._map[event]:
            callback(context)


registry = EventRegistry()


def trigger(event: Event, context: dict, logger: logging.Logger = logger) -> None:
    """Call trigger on main registry."""
    registry.trigger(event, context, logger)


def register(event: Event, callback: Callable[[Context], None]) -> None:
    """Call register on main registry."""
    registry.register(event, callback)
