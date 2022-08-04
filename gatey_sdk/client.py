import requests
import time
import typing
from urllib.parse import urlparse
from urllib.parse import parse_qs
from gatey_sdk.consts import DEFAULT_API_PROVIDER_URL, DEFAULT_API_VERSION
from gatey_sdk.response import Response
from gatey_sdk.exceptions import GateyApiError


class Client:
    """
    Florgon Gatey Client.
    WIP. TBD.
    """

    _api_server_provider_url = DEFAULT_API_PROVIDER_URL
    _api_expected_version = DEFAULT_API_VERSION

    access_token = None

    methods = None

    def __init__(self, *args, **kwargs):
        self.change_api_provider(kwargs.pop("api_provider", DEFAULT_API_PROVIDER_URL))
        self.change_api_version(kwargs.pop("api_version", DEFAULT_API_VERSION))
        self.change_access_token(kwargs.pop("access_token", None))
        self.methods = Methods(client=self)

    def method(self, name: str, **kwargs) -> Response:
        """
        Executes API method with given name.
        """
        url = self._get_method_request_url(name)
        response = self._request_method(
            request_url=url, params=kwargs, method_name=name
        )
        return response

    def capture_exception(self, exception: BaseException):
        return self.methods.capture_exception(exception)

    def capture_message(self, message: str):
        return self.methods.capture_message(message)

    def catch(
        self,
        *,
        reraise: bool = True,
        exception: BaseException | None = None,
        ignored_exceptions: list[BaseException] | None = None,
    ):
        """
        Decorator that catches the exception and captures it as Gatey exception.
        """
        if exception is None:
            exception = BaseException
        if ignored_exceptions is None:
            ignored_exceptions = []

        def decorator(function: typing.Callable):
            def wrapper(*args, **kwargs):
                callable_result = None
                try:
                    callable_result = function(*args, **kwargs)
                except exception as e:
                    for ignored_exception in ignored_exceptions:
                        if type(e) == ignored_exception:
                            return None
                    self.capture_exception(exception=e)
                    if reraise:
                        raise e
                return callable_result

            return wrapper

        return decorator

    def change_access_token(self, access_token: str):
        self.access_token = access_token

    def change_api_provider(self, provider_url: str) -> None:
        """
        Updates API server provider URL.
        Used for self-hosted servers.
        """
        if provider_url.endswith("/"):
            raise ValueError("API provider URL must not end with trailing slash! (/)")
        self._api_server_provider_url = provider_url

    def change_api_version(self, version: str) -> None:
        """
        Updates API version.
        """
        self._api_expected_version = version

    def get_server_time_difference(self) -> int:
        """
        Returns time difference between server and client.
        """
        client_time = time.time()
        server_time = self.methods.utils_get_server_time()
        return server_time - client_time

    def resolve_exception_to_params(self, exception: BaseException) -> typing.Dict:
        """
        Returns dict with parameters for request, from exception.
        """
        return {
            "type": str(type(exception)),
            "call": repr(exception),
            "message": str(exception),
        }

    def api_version_is_current(self) -> bool:
        """
        Returns True, if API version of the server is same with current client API version.
        """
        version = self.method("").get("v")
        return version != self._api_expected_version

    def _parse_access_token_from_redirect_uri(self, redirect_uri: str) -> str:
        """
        Parse access token from OAuth redirect URI where user was redirected.
        """
        parsed_url = urlparse(url=redirect_uri)
        access_token = parse_qs(parsed_url.query).get("access_token", None)
        if access_token:
            return access_token[0]
        return ""

    def _request_method(
        self, request_url, params: typing.Dict[str, typing.Any], method_name: str
    ) -> str:
        """
        Returns JSON response from server.
        """

        response = Response(response=requests.get(url=request_url, params=params))
        error = response.raw_json().get("error", None)
        if error:
            error_message = error.get("message")
            error_code = error.get("code")
            raise GateyApiError(
                f"Failed to call method {method_name}! Error code: {error_code}. Error message: {error_message}"
            )
        return response

    def _get_method_request_url(self, method_name: str):
        """
        Returns method request url.
        """
        return f"{self._api_server_provider_url}/{method_name}"


class Methods:
    """
    Wrapper for API methods.
    """

    client = None

    def __init__(self, client: Client):
        self.client = client

    def utils_get_server_time(self) -> int:
        response = self.client.method("utils.getServerTime")
        return response.raw_json().get("success").get("server_time")

    def capture_exception(self, exception: BaseException):
        response = self.client.method(
            "capture.Exception",
            **self.client.resolve_exception_to_params(exception=exception),
        )
        return response.raw_json().get("success")

    def capture_message(self, message: str):
        response = self.client.method("capture.Message", message=message)
        return response.raw_json().get("success")
