"""
    Main client for Gatey SDK.
    Provides root interface for working with Gatey.
"""
from typing import Callable, Union, Dict, List, Optional

# Utils.
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
    client = gatey_sdk.Client()
    ```
    """

    # If true, will send locals(), globals() variables,
    # alongside with event data.
    capture_vars = True

    # Transport instance.
    # Used for sending instance.
    # Passed with aggregation.
    transport = None

    # Authentication instance.
    # Used for authentication.
    auth = None

    # API instance.
    # Used for sending API HTTP requests.
    api = None

    # Function that will be called when any exception is excepted.
    # Used in global exception handler and catch.
    on_catch_exception_hook = None

    def __init__(
        self,
        *,
        transport: Optional[Union[BaseTransport, Callable]] = None,
        handle_global_exceptions: bool = True,
        global_handler_skip_internal_exceptions: bool = True,
        capture_vars: bool = True,
        access_token: Optional[str] = None,
        project_id: Optional[int] = None,
        server_secret: Optional[str] = None,
        client_secret: Optional[str] = None,
        check_api_auth_on_init: bool = True,
    ):
        """
        :param transport: Transport type argument.
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
        self.capture_vars = capture_vars

        # Default hook event for captured exceptions.
        self.on_catch_exception_hook = lambda exception: self.capture_exception(
            exception=exception
        )

        # Check API auth if requested and should.
        # Notice that auth check is not done when you are using custom transports.
        # (even it is default transport)
        if check_api_auth_on_init is True and transport is None:
            self.api.do_hard_auth_check()

        # Register system exception hook,
        # to handle global exceptions.
        if handle_global_exceptions is True:
            register_system_exception_hook(
                hook=self.on_catch_exception_hook,
                skip_internal_exceptions=global_handler_skip_internal_exceptions,
            )

    def catch(
        self,
        *,
        reraise: bool = True,
        exception: Optional[BaseException] = None,ne,
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

    def capture_event(self, event: Dict, level: str) -> None:
        """
        Captures raw event.
        :param event: Raw event dictionary.
        """
        event_dict = event
        event_dict.update({"level": level})
        event_dict.update(get_additional_event_data())
        self.transport.send_event(event_dict=event)

    def capture_message(self, level: str, message: str) -> None:
        """
        Captures message event.
        :param level: String of the level (INFO, DEBUG, etc)
        :param message: Message string.
        """
        event_dict = {"message": message}
        self.capture_event(event=event_dict, level=level)

    def capture_exception(self, exception: BaseException, *, _level: str = "ERROR"):
        """
        Captures exception event.
        :param exception: Raw exception.
        :param _level: Level of the event that will be sent.
        """
        exception_dict = event_dict_from_exception(
            exception=exception, skip_vars=not self.capture_vars
        )
        event_dict = {"exception": exception_dict}
        if "description" in exception_dict:
            event_dict["message"] = exception_dict["description"]
        self.capture_event(event=event_dict, level=_level)
