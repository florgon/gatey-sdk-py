"""
    Void transport. Does nothing, used as test environment.
"""

from gatey_sdk.transports.base import BaseTransport


class VoidTransport(BaseTransport):
    """
    Void transport. Does nothing, used as test environment.
    """

    @BaseTransport.transport_base_sender_wrapper
    def send_event(self, *args, **kwargs) -> None:
        """
        Handles transport event callback (handle event sending).
        Does nothing.
        """
