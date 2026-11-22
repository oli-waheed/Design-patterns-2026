from dataclasses import dataclass

from domain.events.bus import EventBus


@dataclass(frozen=True)
class Ping:
    value: int


@dataclass(frozen=True)
class Pong:
    value: int


def test_handlers_run_in_subscription_order():
    bus = EventBus()
    calls = []

    bus.subscribe(Ping, lambda event: calls.append(("first", event.value)))
    bus.subscribe(Ping, lambda event: calls.append(("second", event.value)))

    bus.publish(Ping(1))

    assert calls == [("first", 1), ("second", 1)]


def test_publish_only_reaches_handlers_for_that_event_type():
    bus = EventBus()
    calls = []

    bus.subscribe(Pong, lambda event: calls.append(event))

    bus.publish(Ping(1))

    assert calls == []


def test_failing_handler_does_not_block_later_handlers():
    bus = EventBus()
    calls = []

    def broken(event):
        raise RuntimeError("alert writer is down")

    bus.subscribe(Ping, broken)
    bus.subscribe(Ping, lambda event: calls.append(event.value))

    # Does not raise into the publisher.
    bus.publish(Ping(7))

    assert calls == [7]
