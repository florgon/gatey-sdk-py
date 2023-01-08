"""
    Function transport. Calls your function when event sends.
"""

from typing import Callable, Dict
from gatey_sdk.transports.base import BaseTransport
from gatey_sdk.exceptions import GateyTransportError


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

    @BaseTransport.transport_base_sender_wrapper
    def send_event(
        self, event_dict: Dict, skip_to_internal_exception: bool = False
    ) -> None:  # pylint: disable=arguments-differ
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
                )  # pylint: disable=raise-missing-from
            return
        self._function(event_dict)
