"""Event-handling for PyWebnovel."""

import enum
from typing import Callable

from webnovel.utils import Namespace


class Event(enum.Enum):
    """An enum of all PyWebnovel events."""

    UPDATING_EBOOK = "updating-ebook"
    WEBNOVEL_DIR_LOADED = "webnovel-dir-loaded"
    WEBNOVEL_DIR_VALIDATED = "webnovel-dir-validated"
    CREATE_EPUB_START = "create-epub-start"
    CREATE_EPUB_END = "create-epub-end"
    SET_COVER_IMAGE = "set-cover-image"
    SCRAPE_TOTAL_CHAPTERS = "scrape-total-chapters"
    FETCHING_CHAPTERS_START = "fetching-chapters-start"
    FETCHING_CHAPTERS_END = "fetching-chapters-end"
    PROCESS_CHAPTER_BATCH_START = "process-chapter-batch-start"
    PROCESS_CHAPTER_BATCH_END = "process-chapter-batch-end"


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

    def trigger(self, event: Event, context: dict) -> None:
        """Trigger the specified event, running all callbacks."""
        context = Context(context)
        context.event = event
        for callback in self._map[event]:
            callback(context)


registry = EventRegistry()


def trigger(event: Event, context: dict) -> None:
    """Call trigger on main registry."""
    registry.trigger(event, context)


def register(event: Event, callback: Callable[[Context], None]) -> None:
    """Call register on main registry."""
    registry.register(event, callback)
