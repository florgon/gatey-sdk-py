"""
    Custom exceptions that may occur while working with SDK.
"""

from gatey_sdk.response import Response


class GateyApiError(Exception):
    """
    Raised when there is any error with response.
    Means API return error (not success).
    """

    def __init__(
        self,
        message: str,
        error_code: int,
        error_message: str,
        error_status: int,
        response: Response,
    ):
        """
        :param message: Message of the exception.
        :param error_code: API error code
        :param error_message: API error message.
        :param error_status: API error status (HTTP status, from the API `status` error field).
        :param response: API response.
        """
        super().__init__(message)
        self.error_code = error_code
        self.error_message = error_message
        self.error_status = error_status
        self.response = response


class GateyTransportError(Exception):
    """
    Raised when there is any error in the transport.
    For example, raised when `FuncTransport` function raises any exceptions.
    """

    def __init__(self, message: str):
        """
        :param message: Message of the exception.
        """
        super().__init__(message)
