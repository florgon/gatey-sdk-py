"""
    Transport classes, that handles sending events from Gatey.
"""
import json
from typing import Callable, Any, Union, Optional, Dict
from gatey_sdk.exceptions import (
    GateyError,
    GateyTransportError,
    GateyTransportImproperlyConfiguredError,
)
from gatey_sdk.api import Api
from gatey_sdk.auth import Auth


def _transport_base_sender_wrapper(func):
    """
    Wrapper for transports send event methods that converts result to success state.
    """

    def wrapper(*args, **kwargs) -> bool:
        fail_fast = kwargs.pop("__fail_fast", False)
        try:
            func(*args, **kwargs)
        except GateyError as internal_exception:
            if fail_fast:
                raise internal_exception
            return False
        else:
            return True

    return wrapper


class BaseTransport:
    """
    Base transport class. Cannot be used as transport.
    Abstract class for implementing transport classes.
    """

    def __init__(self):
        pass

    @_transport_base_sender_wrapper
    def send_event(self, event_dict: Dict) -> None:
        """
        Handles transport event callback (handle event sending).
        Should be inherited from BaseTransport and implemented in transports.
        """
        raise NotImplementedError()


class HttpTransport(BaseTransport):
    """
    HTTP Transport. Sends event to the Gatey Server when event sends.
    """

    # Allowed aggreation / composition..
    _api_provider: Api = None
    _auth_provider: Optional[Auth] = None

    def __init__(self, api: Optional[Api] = None, auth: Optional[Auth] = None):
        """
        :param api: Api provider.
        :param auth: Authentication provider.
        """

        BaseTransport.__init__(self)
        self._auth_provider = auth if auth else Auth()
        self._api_provider = api if api else Api(self._auth_provider)
        self._check_improperly_configured()

    @_transport_base_sender_wrapper
    def send_event(self, event_dict: Dict) -> None:
        api_params = self._api_params_from_event_dict(event_dict=event_dict)
        self._api_provider.method("event.capture", send_project_auth=True, **api_params)

    def _api_params_from_event_dict(self, event_dict: Dict):
        api_params = {
            "level": event_dict["level"],
        }

        event_params = ["exception", "message", "tags"]

        for param in event_params:
            if param in event_dict:
                api_params[param] = json.dumps(event_dict[param])

        return api_params

    def _check_improperly_configured(self):
        """
        Raises error if auth provider improperly configured for sending event.
        """
        if self._auth_provider.project_id is None:
            raise GateyTransportImproperlyConfiguredError(
                "HttpTransport improperly configured! No project id found in auth provider!"
            )
        if (
            self._auth_provider.server_secret is None
            and self._auth_provider.client_secret is None
        ):
            raise GateyTransportImproperlyConfiguredError(
                "HttpTransport improperly configured! No client / server secret found in auth provider!"
            )


class FuncTransport(BaseTransport):
    """
    Function transport. Calls your function when event sends.
    """

    def __init__(self, func: Callable):
        """
        :param function: Function to call when event sends.
        """
        BaseTransport.__init__(self)
        self._function = func

    @_transport_base_sender_wrapper
    def send_event(
        self, event_dict: Dict, skip_to_internal_exception: bool = False
    ) -> None:
        """
        Handles transport event callback (handle event sending).
        Function transport just takes event and passed it raw to function call.
        """
        if skip_to_internal_exception:
            try:
                self._function(event_dict)
            except Exception as _:
                raise GateyTransportError(
                    f"Unable to handle event send with Function transport (FuncTransport)."
                )
            return
        self._function(event_dict)


class VoidTransport(BaseTransport):
    """
    Void transport. Does nothing, used as test environment.
    """

    @_transport_base_sender_wrapper
    def send_event(self, *args, **kwargs) -> None:
        """
        Handles transport event callback (handle event sending).
        Does nothing.
        """
        pass


class PrintTransport(BaseTransport):
    """
    Print transport. Prints event data, used ONLY as test environment.
    """

    def __init__(
        self,
        indent: int | str | None = 2,
        prepare_event: Callable[[Dict], Dict] | None = None,
        print_function: Callable[[Dict], Any] | None = None,
    ):
        """
        :param function: Function to call when event sends.
        """
        BaseTransport.__init__(self)
        self._indent = indent
        self._prepare_event = prepare_event if prepare_event else lambda e: e
        self._print_function = print_function if print_function else print

    @_transport_base_sender_wrapper
    def send_event(self, event_dict: Dict) -> None:
        """
        Handles transport event callback (handle event sending).
        Print event data.
        """
        dump_data = (
            self._prepare_event(event_dict) if self._prepare_event else event_dict
        )
        print(
            json.dumps(
                dump_data,
                indent=self._indent,
                sort_keys=True,
            )
        )


def build_transport_instance(
    transport_argument: Any = None,
    api: Optional[Api] = None,
    auth: Optional[Auth] = None,
) -> Union[BaseTransport, None]:
    """
    Builds transport instance by transport argument.
    """
    transport_class = None

    if transport_argument is None:
        # If nothing is passed, should be default http transport type.
        return HttpTransport(api=api, auth=auth)

    if isinstance(transport_argument, type) and issubclass(
        transport_argument, BaseTransport
    ):
        # Passed subclass (type) of BaseTransport as transport.
        # Should be instantiated as cls.
        transport_class = transport_argument
        if transport_class in (VoidTransport, PrintTransport):
            return transport_class()
        try:
            return transport_class(api=api, auth=auth)
        except TypeError as _transport_params_error:
            raise GateyTransportImproperlyConfiguredError(
                "Failed to build transport instance. Please instantiate before or except your transport to handle `api`, `auth` params in constructor!"
            ) from _transport_params_error

    if isinstance(transport_argument, BaseTransport):
        # Passed already constructed transport, should do nothing.
        return transport_argument

    if callable(transport_argument):
        # Passed callable (function) as transport.
        # Should be Function transport, as it handles raw function call.
        return FuncTransport(function=transport_argument)

    # Unable to instantiate transport instance.
    raise GateyTransportImproperlyConfiguredError(
        "Failed to build transport instance. Please pass valid transport argument!"
    )
