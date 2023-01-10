"""
    Events `buffer` class, that does storing events (as raw data)
    and handles them passing to the transport.

    Something like `proxy` that can just immediatly send event directly to the transport
    or can buffer them and wait for next requirement in their send right now.

    Includes handling exit signal to not loss any events,
    and flush thread if required (will refresh send every `N` time).
"""
import atexit
from typing import Dict, List, Any, Optional, Callable
from time import sleep
from threading import Thread

from gatey_sdk.transports.base import BaseTransport
from gatey_sdk.consts import (
    DEFAULT_EVENTS_BUFFER_FLUSH_EVERY,
    EVENTS_BUFFER_FLUSHER_THREAD_NAME,
)


class _EventsBufferFlusher:
    """
    Events `buffer` flusher class, does handling auto refresh (every time, at exit).

    Includes handling exit signal to not loss any events,
    and flush thread if required (will refresh send every `N` time).
    """

    # Thread that is used for periodically flushing events to be passed to transport.
    flush_thread: Optional[Thread] = None

    # Settings.
    flush_every: float = DEFAULT_EVENTS_BUFFER_FLUSH_EVERY
    on_flush: Callable[[], Any]

    def __init__(
        self,
        on_flush: Callable[[], Any],
        *,
        flush_every: float = DEFAULT_EVENTS_BUFFER_FLUSH_EVERY
    ):
        """
        :param on_flush: Callable that will be called on flush request.
        :param flush_every: Time in seconds for refreshing and flushing events (passing to the transport), (left 0 to disable)
        """

        # Settings.
        self.on_flush = on_flush
        self.flush_every = float(flush_every)

        # Setup.
        self.ensure_running_thread()
        self.bind_system_exit_hook()

    def ensure_running_thread(self) -> Thread:
        """
        Runs buffer flush thread if it is not running, and returns thread.
        Flush thread is used to send events buffer after some time, not causing to wait core application
        for terminate or new events that will trigger bulk sending (buffer flush).
        :returns Thread: Flush thread.
        """

        if isinstance(self.flush_thread, Thread) and self.flush_thread.is_alive():
            # If thread is currently alive - there is no need to create new thread by removing old reference.
            return self.flush_thread
        return self._spawn_new_thread()

    def flush_thread_target(self) -> None:
        """
        Thread target for events buffer flusher.
        """
        while True:
            sleep(self.flush_every)
            self.on_flush()

    def bind_system_exit_hook(self) -> None:
        """
        Binds system hook for exit (`atexit`).
        Used for sending all buffered events at exit.
        """
        atexit.register(self.on_flush)

    def _spawn_new_thread(self) -> Thread:
        """
        Spawns new thread with removing reference to old one if exists.
        Please use `ensure_running_thread` for safe setup.
        :returns Thread: Flush thread.
        """
        # Thread.
        self.flush_thread = Thread(
            target=self.flush_thread_target,
            args=(),
            name=EVENTS_BUFFER_FLUSHER_THREAD_NAME,
        )

        # Mark thread as daemon (which is required for graceful main thread termination) and start.
        self.flush_thread.daemon = True
        self.flush_thread.start()
        return self.flush_thread


class EventsBuffer:
    """
    Events `buffer` class, that does storing events (as raw data)
    and handles them passing to the transport.

    Something like `proxy` that can just immediatly send event directly to the transport
    or can buffer them and wait for next requirement in their send right now.

    Includes handling exit signal to not loss any events,
    and flush thread if required (will refresh send every `N` time).
    (For that look into `_EventsBufferFlusher`)
    """

    # Settings.
    skip_buffering: bool = True
    max_capacity: int = 0

    # Events data queue that waiting for being passed to the transport.
    # TODO: Research any LIFO structures.
    _events: List[Dict[str, Any]] = []

    # Instances.
    _transport: BaseTransport
    _flusher: _EventsBufferFlusher

    def __init__(
        self,
        transport: BaseTransport,
        *,
        skip_buffering: bool = True,
        max_capacity: int = 0,
        flush_every: float = DEFAULT_EVENTS_BUFFER_FLUSH_EVERY
    ):
        """
        :param transport: Configured transport instance to send events.
        :param skip_buffering: If true, will send (pass) events directly to the transport, without buffering.
        :param max_capacity: Cap for buffer, when that amount of buffered events is reached, will immediatly pass them (left 0 for no capacity)
        :param flush_every: Time in seconds for refreshing and flushing events (passing to the transport), (left 0 to disable)
        """
        # Settings.
        self.skip_buffering = bool(skip_buffering)
        self.max_capacity = int(max_capacity)

        # Store transport instance.
        self._transport = transport
        if not isinstance(self._transport, BaseTransport):
            raise ValueError(
                "`EventsBuffer` expected `transport` to be instance of `BaseTransport`! Please instantiate by own!"
            )

        # Flusher setup.
        self._flusher = _EventsBufferFlusher(
            on_flush=self.send_all, flush_every=flush_every
        )

    def push_event(self, event_dict: Dict) -> bool:
        """
        Collects events.
        Will send immediatly if configured, or just store to send later.

        :param event_dict: Event.
        :returns bool: Returns false if event failed to send or one of another buffered events failed to send.
        """

        # Pass directly if should not buffer.
        if self.skip_buffering:
            return self._send_event(event_dict=event_dict, fail_fast=True)

        # Do buffer and send if required.
        self._store_event(event_dict=event_dict)
        if self.is_full():
            return self.send_all()
        return True

    def clear_events(self) -> None:
        """
        Drops (removes) all buffered events explicitly if any.
        WARNING: This will skip sending, use only if you know what this does!
        """
        self._events = []

    def is_empty(self) -> bool:
        """
        Returns is buffer is empty or not.
        :returns bool: Is empty or not.
        """
        return len(self._events) == 0

    def is_full(self) -> bool:
        """
        Returns is events buffer is full and should send all to the transport.
        :returns bool: Is full.
        """
        if self.max_capacity is None or self.max_capacity == 0:
            return False
        return len(self._events) >= self.max_capacity

    def send_all(self) -> bool:
        """
        Sends all buffered events if any.
        :returns bool: Returns is all events was sent.
        """
        events_to_send = self._events.copy()
        self.clear_events()

        # Build events based on non-sent events.
        self._events = [
            event
            for event in events_to_send
            if not self._send_event(event_dict=event, fail_fast=False)
        ]

        return self.is_empty()

    def _store_event(self, event_dict: Dict) -> None:
        """
        Stores event to events storage.
        :param event_dict: Event.
        """
        self._events.append(event_dict)

    def _send_event(self, event_dict: Dict, *, fail_fast: bool = False) -> bool:
        """
        Sends event with transport.
        :param event_dict: Event.
        :param fail_fast: If true, will raise exception rather and returning success / failure (TODO: Remove).
        """
        # TODO: Remove `__fail_fast`, research better solution for decorating or remove that feature.
        return self._transport.send_event(event_dict=event_dict, __fail_fast=fail_fast)


__all__ = ["EventsBuffer"]
