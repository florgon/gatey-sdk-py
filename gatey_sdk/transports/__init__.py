"""
    Transports for Client.
"""

from typing import Any, Union, Optional

from gatey_sdk.transports.base import BaseTransport
from gatey_sdk.transports.http import HttpTransport
from gatey_sdk.transports.func import FuncTransport
from gatey_sdk.transports.void import VoidTransport
from gatey_sdk.transports.print import PrintTransport

from gatey_sdk.exceptions import (
    GateyTransportImproperlyConfiguredError,
)
from gatey_sdk.api import Api
from gatey_sdk.auth import Auth


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
        return FuncTransport(func=transport_argument)

    # Unable to instantiate transport instance.
    raise GateyTransportImproperlyConfiguredError(
        "Failed to build transport instance. Please pass valid transport argument!"
    )


# Base transport should be used as typing
# (polymorphism for expecting any implementation of abstract class as interface)
# You are not supposed to implement own class-transports (as there is always no need for that)
# use FuncTransport with your function, to make work done with native library implementation.
__all__ = [
    # Typing.
    "BaseTransport",
    # Default.
    "HttpTransport",
    # Debug.
    "FuncTransport",
    "PrintTransport",
    "VoidTransport",
]
