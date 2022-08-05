# NOT REFACTORED.

from typing import Callable, Union, Dict

from gatey_sdk.platform import Platform

# Utils.
from gatey_sdk.consts import SDK_INFORMATION_DICT
from gatey_sdk.utils import (
    get_trace_from_traceback,
    get_variables_from_traceback,
    wrap_in_exception_handler,
    register_system_exception_hook,
)

# Components.
from gatey_sdk.api import Api
from gatey_sdk.auth import Auth
from gatey_sdk.transport import build_transport_instance, BaseTransport


class Client:
    """ """

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
        transport: Union[BaseTransport, Callable] = None,
        handle_global_exceptions: bool = True,
    ):
        """
        :param transport: Transport type argument.
        """

        # Components.
        self.api = Api()
        self.auth = Auth()
        self.transport = build_transport_instance(transport_argument=transport)

        # Default hook event for captured exceptions.
        self.on_catch_exception_hook = lambda exception: self.capture_exception(
            exception=exception
        )

        # Register system exception hook,
        # to handle global exceptions.
        if handle_global_exceptions is True:
            register_system_exception_hook(hook=self.on_catch_exception_hook)

    def catch(
        self,
        *,
        reraise: bool = True,
        exception: BaseException | None = None,
        ignored_exceptions: list[BaseException] | None = None,
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

    # Code below is not refactored.
    # Code below is not refactored.
    # Code below is not refactored.
    # Code below is not refactored.
    # Code below is not refactored.

    def capture_exception(self, exception: BaseException):
        self.transport.on_event_send()

    def capture_message(self, message: str):
        self.transport.on_event_send()

    def resolve_exception_to_params(
        self, exception: BaseException, include_vars: bool = True
    ) -> Dict:
        exc_traceback = exception.__traceback__
        traceback_vars = (
            get_variables_from_traceback(traceback=exc_traceback)
            if include_vars
            else {"locals": [], "globals": []}
        )
        traceback = get_trace_from_traceback(exc_traceback)
        return {
            "type": str(type(exception).__name__),
            "message": str(exception),
            "tags": self._get_tags(),
            "platform": Platform.get_platform(),
            "runtime": Platform.get_runtime(),
            "sdk": SDK_INFORMATION_DICT,
            "vars": traceback_vars,
            "traceback": traceback,
        }

    def _get_tags(self) -> Dict:
        tags = {}
        tags.update(Platform.get_platform_dependant_tags())
        return tags
