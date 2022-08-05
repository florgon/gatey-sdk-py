"""
    Transport classes, that handles sending events from Gatey.
"""

from typing import Callable, Any, Union, Optional, Dict
from gatey_sdk.exceptions import GateyTransportError
from gatey_sdk.api import Api


class BaseTransport:
    """
    Base transport class. Cannot be used as transport.
    Abstract class for implementing transport classes.
    """

    def __init__(self):
        pass

    def send_event(self, event_dict: Dict):
        """
        Handles transport event callback (handle event sending).
        Should be inherited from BaseTransport and implemented in transports.
        """
        raise NotImplementedError()


class HttpTransport(BaseTransport):
    """
    HTTP Transport. Sends event to the Gatey Server when event sends.
    """

    def __init__(self, api: Optional[Api] = None):
        """ """
        BaseTransport.__init__(self)
        self._api = api if api else Api()

    def send_event(self, event_dict: Dict):
        return self._api.method("event.Capture")


class FuncTransport(BaseTransport):
    """
    Function transport. Calls your function when event sends.
    """

    def __init__(self, function: Callable):
        """
        :param function: Function to call when event sends.
        """
        BaseTransport.__init__(self)
        self._function = function

    def send_event(self, event_dict: Dict) -> None:
        """
        Handles transport event callback (handle event sending).
        Function transport just takes event and passed it raw to function call.
        """
        try:
            self._function(event_dict)
        except Exception as transport_exception:
            raise GateyTransportError(
                f"Unable to handle event send with Function transport (FuncTransport). Raised exception: {transport_exception}"
            )


def build_transport_instance(
    transport_argument: Any = None,
) -> Union[BaseTransport, None]:
    """
    Builds transport instance by transport argument.
    """
    transport_class = None

    if transport_argument is None:
        # If nothing is passed, should be default http transport type.
        return HttpTransport()

    if isinstance(transport_argument, type) and issubclass(
        transport_argument, BaseTransport
    ):
        # Passed subclass of BaseTransport as transport.
        # Should be instantiated as cls.
        transport_class = transport_argument
        return transport_class()

    if callable(transport_argument):
        # Passed callable (function) as transport.
        # Should be Function transport, as it handles raw function call.
        return FuncTransport(function=transport_argument)

    # Unable to instantiate transport instance.
    return None
