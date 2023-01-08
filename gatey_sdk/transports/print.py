"""
    Print transport. Prints event data, used ONLY as test environment.
"""

import json
from typing import Callable, Any, Dict, Optional, Union
from gatey_sdk.transports.base import BaseTransport


class PrintTransport(BaseTransport):
    """
    Print transport. Prints event data, used ONLY as test environment.
    """

    def __init__(
        self,
        indent: Optional[Union[int, str]] = 2,
        prepare_event: Optional[Callable[[Dict], Dict]] = None,
        print_function: Optional[Callable[[Dict], Any]] = None,
    ):
        """
        :param indent: Indent for json convertion
        :param prepare_event: Function that will be called with event and should return event (can be used for clearing unused data to print)
        :param print_function: Function to pass prepared event data to.
        """
        BaseTransport.__init__(self)
        self._indent = indent
        self._prepare_event = prepare_event if prepare_event else lambda e: e
        self._print_function = print_function if print_function else print

    @BaseTransport.transport_base_sender_wrapper
    def send_event(self, event_dict: Dict) -> None:
        """
        Handles transport event callback (handle event sending).
        Print event data.
        """
        print(
            json.dumps(
                self._prepare_event(event_dict),
                indent=self._indent,
                sort_keys=True,
            )
        )
