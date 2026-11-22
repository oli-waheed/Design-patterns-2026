import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any


logger = logging.getLogger(__name__)

Handler = Callable[[Any], None]


class EventBus:
    """In-process publish/subscribe event bus (the Observer subject).

    Publishers only know the bus and the event; they never know which
    subscribers exist. Handlers for one event class run in subscription
    order.
    """

    def __init__(self) -> None:
        self._handlers: dict[type, list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: object) -> None:
        # Copy the list so a handler that subscribes during publish does
        # not change this delivery.
        for handler in list(self._handlers.get(type(event), [])):
            try:
                handler(event)
            except Exception:
                # One failing subscriber must not stop the others
                # (for example a later WebSocket subscriber in Phase 12),
                # and must not fail the publisher's already-saved work.
                logger.exception(
                    "Event handler %r failed for %s",
                    handler,
                    type(event).__name__,
                )
