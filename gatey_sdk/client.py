"""
    Main client for Gatey SDK.
    Provides root interface for working with Gatey.
"""

from typing import Callable, Union, Dict, List, Optional, Any

# Utils.
from gatey_sdk.utils import (
    get_additional_event_tags,
)
from gatey_sdk.consts import DEFAULT_EVENTS_BUFFER_FLUSH_EVERY
from gatey_sdk.internal.exc import (
    wrap_in_exception_handler,
    register_system_exception_hook,
    event_dict_from_exception,
)

# Components.
from gatey_sdk.api import Api
from gatey_sdk.auth import Auth
from gatey_sdk.transports import build_transport_instance, BaseTransport
from gatey_sdk.buffer import EventsBuffer


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
    transport: BaseTransport
    auth: Auth
    api: Api
    events_buffer: EventsBuffer

    # Settings.
    kwargs_settings: Dict[str, Any] = dict()
    exceptions_capture_vars = True
    exceptions_capture_code_context = True
    include_runtime_info = True
    include_platform_info = True
    include_sdk_info = True
    default_tags_context = dict()

    def __init__(
        self,
        *,
        transport: Optional[Union[BaseTransport, Callable]] = None,
        # Settings.
        global_handler_skip_internal_exceptions: bool = True,
        buffer_events_for_bulk_sending: bool = False,
        buffer_events_max_capacity: int = 3,
        buffer_events_flush_every: float = DEFAULT_EVENTS_BUFFER_FLUSH_EVERY,
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
        # Other params.
        **kwargs_settings,
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
        self.api = Api(
            auth=self.auth, **kwargs_settings.get("api_instance_kwargs", dict())
        )
        self.transport = build_transport_instance(
            transport_argument=transport, api=self.api, auth=self.auth
        )
        self.events_buffer = EventsBuffer(
            transport=self.transport,
            skip_buffering=not buffer_events_for_bulk_sending,
            max_capacity=buffer_events_max_capacity,
            flush_every=buffer_events_flush_every,
        )

        # Options.
        self.exceptions_capture_vars = exceptions_capture_vars
        self.exceptions_capture_code_context = exceptions_capture_code_context
        self.include_runtime_info = include_runtime_info
        self.include_platform_info = include_platform_info
        self.include_sdk_info = include_sdk_info
        self.kwargs_settings = kwargs_settings.copy()

        # Tags like platform, sdk, etc.
        self.default_tags_context = self._build_default_tags_context(
            foreign_tags=kwargs_settings.get("default_tags_context", dict())
        )

        # Check API auth if requested and should.
        # Notice that auth check is not done when you are using custom transports.
        # (even it is default transport)
        if check_api_auth_on_init is True and transport is None:
            self.api.do_hard_auth_check()

        # Register system hooks.
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
        # return self._buffer_captured_event(event_dict=event_dict)
        self.events_buffer.push_event(event_dict=event_dict)

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

    def bulk_send_buffered_events(self) -> bool:
        """
        Sends all buffered events.
        Returns is all events was sent.
        """
        return self.events_buffer.send_all()

    def force_drop_buffered_events(self) -> None:
        """
        Drops (removes) buffered events explicitly.
        """
        return self.events_buffer.clear_events()

    def _on_catch_exception_hook(self, exception) -> bool:
        """
        Hook that will be called when catched exception.
        (except via `capture_exception`)
        """
        return self.capture_exception(exception=exception)


Client = _Client
