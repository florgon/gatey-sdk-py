"""
    Custom exceptions that may occur while working with SDK.
"""
from requests import Response as _HttpResponse
from gatey_sdk.response import Response
from gatey_sdk.consts import EXC_ATTR_IS_INTERNAL


class GateyError(Exception):
    """
    Super class for Gatey exceptions.
    """


class GateyHttpError(GateyError):
    """
    Raised when there is any error with HTTP call.
    """

    def __init__(self, message: str, raw_response: _HttpResponse):
        """
        :param message: Message of the exception.
        :param raw_response: Raw HTTP response.
        """
        super().__init__(message)
        self.raw_response = raw_response
        setattr(self, EXC_ATTR_IS_INTERNAL, True)


class GateyApiError(GateyHttpError):
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
        raw_response: _HttpResponse,
    ):
        """
        :param message: Message of the exception.
        :param error_code: API error code
        :param error_message: API error message.
        :param error_status: API error status (HTTP status, from the API `status` error field).
        :param response: API response.
        """
        super().__init__(message, raw_response=raw_response)
        self.error_code = error_code
        self.error_message = error_message
        self.error_status = error_status
        self.response = response
        setattr(self, EXC_ATTR_IS_INTERNAL, True)


class GateyApiResponseError(GateyHttpError):
    """
    Raised when there is any error in the procesing response fro the API.
    """

    def __init__(self, message: str, raw_response: _HttpResponse):
        """
        :param message: Message of the exception.
        """
        super().__init__(message, raw_response)
        setattr(self, EXC_ATTR_IS_INTERNAL, True)


class GateyApiAuthError(GateyError):
    """
    Raised when there is any error in the auth to the API.
    """

    def __init__(self, message: str):
        """
        :param message: Message of the exception.
        """
        super().__init__(message)
        setattr(self, EXC_ATTR_IS_INTERNAL, True)


class GateyTransportError(GateyError):
    """
    Raised when there is any error in the transport.
    For example, raised when `FuncTransport` function raises any exceptions.
    """

    def __init__(self, message: str):
        """
        :param message: Message of the exception.
        """
        super().__init__(message)
        setattr(self, EXC_ATTR_IS_INTERNAL, True)


class GateyTransportImproperlyConfiguredError(GateyTransportError):
    """
    Raised when there is any error in the transport configuration.
    For example, raised when no project id or client / server secret.
    """

    def __init__(self, message: str):
        """
        :param message: Message of the exception.
        """
        super().__init__(message)
        setattr(self, EXC_ATTR_IS_INTERNAL, True)
