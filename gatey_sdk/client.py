"""
    Main client for Gatey SDK.
    Provides root interface for working with Gatey.
"""

import atexit
from threading import Thread
from time import sleep
from typing import Callable, Union, Dict, List, Optional, Any

# Utils.
from gatey_sdk.utils import (
    get_additional_event_tags,
)
from gatey_sdk.internal.exc import (
    wrap_in_exception_handler,
    register_system_exception_hook,
    event_dict_from_exception,
)


# Components.
from gatey_sdk.api import Api
from gatey_sdk.auth import Auth
from gatey_sdk.transports import build_transport_instance, BaseTransport


class _Client:
    """
    ## Gatey SDK client.
    Main interface for working with Gatey.
    Provides transport, auth, api interfaces.

    ### Example use:
    ```python
    import gatey_sdk
    client = gatey_sdk.Client(...)
    ```
    """

    # Instances.
    transport = None  # Used for sending instance (Passed with aggregation).
    auth = None  # Used for authentication.
    api = None  # Used for sending API HTTP requests.

    # Events data queue that waiting for being sent to server.
    _events_buffer: List[Dict[str, Any]] = []
    _events_buffer_flush_thread: Optional[Thread] = None

    # Settings.

    # If true, will send locals(), globals() variables,
    # alongside with event data.
    exceptions_capture_vars = True

    # If true, will capture source code lines for exception.
    exceptions_capture_code_context = True

    # Buffering settings for bulk sending.
    buffer_events_for_bulk_sending = None
    buffer_events_max_capacity = 0
    buffer_events_flush_every = 10.0

    # Include event data.
    include_runtime_info = True
    include_platform_info = True
    include_sdk_info = True

    # Default tags.
    default_tags_context = dict()

    def __init__(
        self,
        *,
        transport: Optional[Union[BaseTransport, Callable]] = None,
        # Settings.
        global_handler_skip_internal_exceptions: bool = True,
        buffer_events_for_bulk_sending: bool = False,
        buffer_events_max_capacity: int = 3,
        buffer_events_flush_every: float = 10.0,
        handle_global_exceptions: bool = False,
        include_runtime_info: bool = True,
        include_platform_info: bool = True,
        include_sdk_info: bool = True,
        exceptions_capture_vars: bool = False,
        exceptions_capture_code_context: bool = True,
        # User auth settings.
        access_token: Optional[str] = None,
        # SDK auth settings.
        project_id: Optional[int] = None,
        server_secret: Optional[str] = None,
        client_secret: Optional[str] = None,
        check_api_auth_on_init: bool = True,
    ):
        """
        :param transport: BaseTransport layer for sending event to the server / whatever else.
        :param global_handler_skip_internal_exceptions:
        :param buffer_events_for_bulk_sending: Will buffer all events (not send immediatly) and will do bulk send when this is required (at exit, or when reached buffer max cap)
        :param buffer_events_max_capacity: Maximal size of buffer to do bulk sending (left 0 for no cap).
        :param handle_global_exceptions: Will catch all exception (use system hook for that).
        :param include_runtime_info: If true, will send runtime information.
        :param include_platform_info: If true will send platform information.
        :param include_sdk_info: If true will send SDK information.
        :param exceptions_capture_vars: Will capture variable (globals, locals) for all exceptions.
        :param exceptions_capture_code_context: Will capture source code context (lines).
        :param access_token: User access token for calling API as authorized user (not for catching events).
        :param project_id: ID of the project from Gatey dashboard.
        :param server_secret: From Gatey dashboard.
        :param client_secret: From Gatey dashboard.
        :param check_api_auth_on_init: Will do hard auth check at init.
        """

        # Components.
        self.auth = Auth(
            access_token=access_token,
            project_id=project_id,
            server_secret=server_secret,
            client_secret=client_secret,
        )
        self.api = Api(auth=self.auth)
        self.transport = build_transport_instance(
            transport_argument=transport, api=self.api, auth=self.auth
        )

        # Options.
        self.exceptions_capture_vars = exceptions_capture_vars
        self.exceptions_capture_code_context = exceptions_capture_code_context
        self.buffer_events_for_bulk_sending = buffer_events_for_bulk_sending
        self.buffer_events_max_capacity = buffer_events_max_capacity
        self.buffer_events_flush_every = buffer_events_flush_every
        self.include_runtime_info = include_runtime_info
        self.include_platform_info = include_platform_info
        self.include_sdk_info = include_sdk_info

        # Tags like platform, sdk, etc.
        self.default_tags_context = self._build_default_tags_context(
            foreign_tags=dict()
        )

        # Check API auth if requested and should.
        # Notice that auth check is not done when you are using custom transports.
        # (even it is default transport)
        if check_api_auth_on_init is True and transport is None:
            self.api.do_hard_auth_check()

        # Register system hooks.
        self._bind_system_exit_hook()
        if handle_global_exceptions is True:
            register_system_exception_hook(
                hook=self._on_catch_exception_hook,
                skip_internal_exceptions=global_handler_skip_internal_exceptions,
            )

        # Start flush thread for bulk sending after timeout (every N).
        if self.buffer_events_for_bulk_sending:
            self._ensure_running_buffer_flush_thread()

    def catch(
        self,
        *,
        reraise: bool = True,
        exception: Optional[BaseException] = None,
        ignored_exceptions: Optional[List[BaseException]] = None,
        skip_global_handler_on_ignore: bool = False,
    ):
        """
        Decorator that catches the exception and captures it as Gatey exception.
        :param reraise: If False, will not raise the exception again, application will not fall (WARNING: USE THIS WISELY TO NOT GET UNEXPECTED BEHAVIOR)
        :param exception: Target exception type to capture.
        :param ignored_exceptions: List of exceptions that should not be captured.
        :param skip_global_handler_on_ignore: If true, will skip global exception handler if exception was ignored.
        """
        return wrap_in_exception_handler(
            reraise=reraise,
            exception=exception,
            ignored_exceptions=ignored_exceptions,
            skip_global_handler_on_ignore=skip_global_handler_on_ignore,
            on_catch_exception=self._on_catch_exception_hook,
        )

    def capture_event(
        self,
        event: Dict,
        level: str,
        tags: Optional[Dict[str, str]] = None,
        include_default_tags: bool = True,
    ) -> bool:
        """
        Captures raw event data and passes it to the transport.
        You should not use this function directly, please use `capture_message` or `capture_exception`!
        This function is used as low-level call to capture all events.

        :param event: Raw event dictionary that will be updated with base event data (including tags).
        :param level: Level of the event.
        :param tags: Dictionary of the tags (string-string).
        :param include_default_tags: If false, will force to not pass default tags context of the client to the event.
        """
        if tags is None or not isinstance(tags, Dict):
            tags = dict()

        if not isinstance(level, str):
            raise TypeError("Level of the event should be always string!")
        if not isinstance(event, Dict):
            raise TypeError("Event data should be Dict!")

        # Include default tags if requred.
        tags.update(self.default_tags_context if include_default_tags else {})

        # Build event data.
        event_dict = event.copy()
        event_dict["tags"] = tags
        event_dict["level"] = level.lower()

        # Will buffer or immediatly send event.
        return self._buffer_captured_event(event_dict=event_dict)

    def capture_message(
        self,
        message: str,
        level: str = "info",
        *,
        tags: Optional[Dict[str, str]] = None,
        include_default_tags: bool = True,
    ) -> bool:
        """
        Captures message event.
        :param level: String of the level (INFO, DEBUG, etc)
        :param message: Message string.
        :param tags: Dictionary of the tags (string-string).
        :param include_default_tags: If false, will force to not pass default tags context of the client to the event.
        """
        event_dict = {"message": message}
        return self.capture_event(
            event=event_dict,
            level=level,
            tags=tags,
            include_default_tags=include_default_tags,
        )

    def capture_exception(
        self,
        exception: BaseException,
        *,
        level: str = "error",
        tags: Optional[Dict[str, str]] = None,
        include_default_tags: bool = True,
    ) -> bool:
        """
        Captures exception event.
        :param exception: Raw exception.
        :param level: Level of the event that will be sent.
        :param tags: Dictionary of the tags (string-string).
        :param include_default_tags: If false, will force to not pass default tags context of the client to the event.
        """
        exception_dict = event_dict_from_exception(
            exception=exception,
            skip_vars=not self.exceptions_capture_vars,
            include_code_context=self.exceptions_capture_code_context,
        )
        event_dict = {"exception": exception_dict}
        if "description" in exception_dict:
            event_dict["message"] = exception_dict["description"]
        return self.capture_event(
            event=event_dict,
            level=level,
            tags=tags,
            include_default_tags=include_default_tags,
        )

    def update_default_tag(self, tag_name: str, tag_value: str) -> None:
        """
        Updates default value for tag.
        """
        if not isinstance(tag_value, str) or not isinstance(tag_name, str):
            raise TypeError("Tag name and value should be strings!")
        self.default_tags_context[tag_name] = tag_value

    def bulk_send_buffered_events(self) -> bool:
        """
        Sends all buffered events.
        Returns is all events was sent.
        """

        # Copy buffer and clear it.
        events_bulk_queue = self._events_buffer.copy()
        self._events_buffer = []

        for event_dict in events_bulk_queue:
            if not self.transport.send_event(event_dict=event_dict):
                # If failed, pass back.
                self._events_buffer.append(event_dict)
        return len(self._events_buffer) == 0

    def force_drop_buffered_events(self) -> None:
        """
        Drops (removes) buffered events explicitly.
        """
        self._events_buffer = []

    def _build_default_tags_context(
        self, foreign_tags: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Returns default tags dict (context).
        """
        default_tags = dict()
        default_tags = get_additional_event_tags(
            include_runtime_info=self.include_runtime_info,
            include_platform_info=self.include_runtime_info,
            include_sdk_info=self.include_sdk_info,
        )
        default_tags.update(foreign_tags)
        return default_tags

    def _ensure_running_buffer_flush_thread(self) -> Thread:
        """
        Runs buffer flush thread is it not running, and returns thread.
        Flush thread is used to send events buffer after some time, not causing to wait core application
        for terminate or new events that will trigger bulk sending (buffer flush).
        """

        if (
            isinstance(self._events_buffer_flush_thread, Thread)
            and self._events_buffer_flush_thread.is_alive()
        ):
            # If thread is currently alive - there is no need to create new thread by removing old reference.
            return self._events_buffer_flush_thread

        # Thread.
        self._events_buffer_flush_thread = Thread(
            target=self._buffer_flush_thread_target,
            args=(),
            name="gatey_sdk.events_buffer.flusher",
        )

        # Mark thread as daemon (which is required for graceful main thread termination) and start.
        self._events_buffer_flush_thread.daemon = True
        self._events_buffer_flush_thread.start()

        return self._events_buffer_flush_thread

    def _buffer_flush_thread_target(self) -> None:
        """
        Thread target for events buffer flusher.
        """
        while True:
            sleep(self.buffer_events_flush_every)
            self.bulk_send_buffered_events()

    def _on_catch_exception_hook(self, exception):
        """
        Hook that will be called when catched exception.
        (except via `capture_exception`)
        """
        return self.capture_exception(exception=exception)

    def _bind_system_exit_hook(self) -> None:
        """
        Binds system hook for exit.
        """

        # Bulk send buffered events at exit.
        if self.buffer_events_for_bulk_sending:
            atexit.register(self.bulk_send_buffered_events)

    def _events_buffer_is_full(self) -> bool:
        """
        Returns is events buffer is full and should be bulk sent.
        """
        if (
            self.buffer_events_max_capacity is None
            or self.buffer_events_max_capacity == 0
        ):
            return False
        return len(self._events_buffer) >= self.buffer_events_max_capacity

    def _buffer_captured_event(self, event_dict: Dict) -> bool:
        """
        Buffers captured event for bulk sending later.
        """

        # Pass directly if should not buffer.
        if not self.buffer_events_for_bulk_sending:
            return self.transport.send_event(event_dict=event_dict, __fail_fast=True)

        # Do buffer and send if required.
        self._events_buffer.append(event_dict)
        if self._events_buffer_is_full():
            return self.bulk_send_buffered_events()
        return True


Client = _Client
