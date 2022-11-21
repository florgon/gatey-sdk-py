"""
    Main client for Gatey SDK.
    Provides root interface for working with Gatey.
"""

import atexit
from typing import Callable, Union, Dict, List, Optional

# Utils.
from gatey_sdk.exceptions import GateyError
from gatey_sdk.utils import (
    wrap_in_exception_handler,
    register_system_exception_hook,
    event_dict_from_exception,
    get_additional_event_data,
)

# Components.
from gatey_sdk.api import Api
from gatey_sdk.auth import Auth
from gatey_sdk.transport import build_transport_instance, BaseTransport


class Client:
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
    _events_buffer: List[Dict] = []

    # Settings.

    # If true, will send locals(), globals() variables,
    # alongside with event data.
    exceptions_capture_vars = True

    # Buffering settings for bulk sending.
    buffer_events_for_bulk_sending = None
    buffer_events_max_capacity = 0

    def __init__(
        self,
        *,
        transport: Optional[Union[BaseTransport, Callable]] = None,
        # Settings.
        global_handler_skip_internal_exceptions: bool = True,
        buffer_events_for_bulk_sending: bool = True,
        buffer_events_max_capacity: int = 3,
        handle_global_exceptions: bool = True,
        exceptions_capture_vars: bool = True,
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
        :param exceptions_capture_vars: Will capture variable (globals, locals) for all exceptions.
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
        self.buffer_events_for_bulk_sending = buffer_events_for_bulk_sending
        self.buffer_events_max_capacity = buffer_events_max_capacity

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
            on_catch_exception=self.on_catch_exception_hook,
        )

    def capture_event(self, event: Dict, level: str) -> bool:
        """
        Captures raw event.
        :param event: Raw event dictionary.
        :param level: Level of the event.
        """
        event_dict = event
        event_dict.update({"level": level})
        event_dict.update(get_additional_event_data())

        # Will buffer or immediatly send event.
        return self._buffer_captured_event(event_dict=event_dict)

    def capture_message(self, level: str, message: str) -> bool:
        """
        Captures message event.
        :param level: String of the level (INFO, DEBUG, etc)
        :param message: Message string.
        """
        event_dict = {"message": message}
        return self.capture_event(event=event_dict, level=level)

    def capture_exception(
        self, exception: BaseException, *, _level: str = "ERROR"
    ) -> int:
        """
        Captures exception event.
        :param exception: Raw exception.
        :param _level: Level of the event that will be sent.
        """
        exception_dict = event_dict_from_exception(
            exception=exception, skip_vars=not self.exceptions_capture_vars
        )
        event_dict = {"exception": exception_dict}
        if "description" in exception_dict:
            event_dict["message"] = exception_dict["description"]
        return self.capture_event(event=event_dict, level=_level)

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

    def _buffer_captured_event(self, event_dict: Dict) -> None:
        """
        Buffers captured event for bulk sending later.
        """

        # Pass directly if should not buffer.
        if not self.buffer_events_for_bulk_sending:
            return self.transport.send_event(event_dict=event_dict)

        # Do buffer and send if required.
        self._events_buffer.append(event_dict)
        if self._events_buffer_is_full():
            return self.bulk_send_buffered_events()
        return True
