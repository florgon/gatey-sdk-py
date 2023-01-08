"""
    Base abstract class for all transports.
"""

from typing import Dict, Callable, Any
from gatey_sdk.exceptions import GateyError

# There is need in typing.ParamSpec which is 3.10 feature,
# that is not supported in <=3.9, need better way to type hint decorated method.


# Above public field because of requirements below.
def _transport_base_sender_wrapper(
    func: Callable[[Dict], Any]
) -> Callable[[Dict], bool]:
    """
    Wrapper for transport send event method that converts result to success state (boolean).
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

    # -> BaseTransport.transport_base_sender_wrapper
    # For inherited.
    @_transport_base_sender_wrapper
    def send_event(self, event_dict: Dict) -> None:
        """
        Handles transport event callback (handle event sending).
        Should be inherited from BaseTransport and implemented in transports.
        """
        raise NotImplementedError()

    @staticmethod
    def transport_base_sender_wrapper(
        func: Callable[[Dict], Any]
    ) -> Callable[[Dict], bool]:
        """
        Wrapper for transports send event methods that converts result to success state.
        """
        return _transport_base_sender_wrapper(func)


__all__ = ["BaseTransport"]
