# pylint: disable=arguments-differ
# pylint: disable=raise-missing-from
"""
    Function transport. Calls your function when event sends.
"""

from typing import Callable, Dict, Any
from gatey_sdk.transports.base import BaseTransport
from gatey_sdk.exceptions import GateyTransportError


class FuncTransport(BaseTransport):
    """
    Function transport. Calls your function when event sends.
    """

    skip_to_internal_exception: bool = False
    _function: Callable[..., Any]

    def __init__(self, func: Callable, *, skip_to_internal_exception: bool = False):
        """
        :param function: Function to call when event sends.
        """
        BaseTransport.__init__(self)
        self.skip_to_internal_exception = skip_to_internal_exception
        self._function = func

    @BaseTransport.transport_base_sender_wrapper
    def send_event(self, event_dict: Dict) -> None:
        """
        Handles transport event callback (handle event sending).
        Function transport just takes event and passed it raw to function call.
        """
        if self.skip_to_internal_exception:
            try:
                self._function(event_dict)
            except Exception as _:
                raise GateyTransportError(
                    "Unable to handle event send with Function transport (FuncTransport)."
                )
            return
        self._function(event_dict)
