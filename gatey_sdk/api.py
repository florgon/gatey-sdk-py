"""
    API class for working with API (HTTP).
    Sends HTTP requests, handles API methods.
"""
from typing import Optional
import requests

from gatey_sdk.auth import Auth
from gatey_sdk.response import Response
from gatey_sdk.exceptions import GateyApiError
from gatey_sdk.utils import remove_trailing_slash
from gatey_sdk.consts import (
    API_DEFAULT_SERVER_PROVIDER_URL,
    API_DEFAULT_SERVER_EXPECTED_VERSION,
)


class Api:
    """
    Wrapper for API methods, HTTP sender.
    """

    # URL of the API.
    # Can be changed for Self-Hosted servers.
    _api_server_provider_url = API_DEFAULT_SERVER_PROVIDER_URL

    # Version that expected from the API.
    _api_server_expected_version = API_DEFAULT_SERVER_EXPECTED_VERSION

    # `Auth` instance that provides authentication fields.
    _auth_provider: Auth = None

    def __init__(self, auth: Optional[Auth] = None):
        """
        :param auth: Auth provider as the `Auth` instance.
        """
        if not isinstance(auth, Auth):
            raise TypeError(
                "Auth must be an instance of `Auth`! You may not pass auth as it will be initialise blank internally in `Api`."
            )
        self._auth_provider = auth if auth else Auth()

    def method(
        self,
        name: str,
        *,
        send_access_token: bool = False,
        send_project_auth: bool = False,
        **kwargs,
    ) -> Response:
        """
        Executes API method with given name.
        And then return response from it.
        :param name: Name of the method to call.
        """

        # Build URL where API method is located.
        api_server_method_url = f"{self._api_server_provider_url}/{name}"

        http_params = kwargs.copy()
        if send_access_token and self._auth_provider:
            if self._auth_provider.access_token:
                http_params.update({"access_token": self._auth_provider.access_token})

        if send_project_auth and not send_access_token and self._auth_provider:
            if self._auth_provider.project_id:
                http_params.update({"project_id": self._auth_provider.project_id})
            if self._auth_provider.server_secret:
                http_params.update({"server_secret": self._auth_provider.server_secret})
            if (
                self._auth_provider.client_secret
                and not self._auth_provider.server_secret
            ):
                http_params.update({"client_secret": self._auth_provider.client_secret})

        # Send HTTP request.
        http_response = requests.get(url=api_server_method_url, params=http_params)

        # Wrap HTTP response in to own Response object.
        response = Response(http_response=http_response)

        # Raise exception if there is any error returned with Api.
        self._process_error_and_raise(method_name=name, response=response)

        return response

    def change_api_server_provider_url(self, provider_url: str) -> None:
        """
        Updates API server provider URL.
        Used for self-hosted servers.
        :param provider_url: URL of the server API provider.
        """
        provider_url = remove_trailing_slash(provider_url)
        self._api_server_provider_url = provider_url

    def change_api_server_expected_version(self, version: str) -> None:
        """
        Updates API version.
        :param version: Version of API.
        """
        self._api_server_expected_version = version

    def _process_error_and_raise(self, method_name: str, response: Response) -> None:
        """
        Processes error, and if there is any error, raise ApiError exception.
        """
        error = response.raw_json().get("error", None)
        if error:
            # If there is an error.

            # Query error fields.
            error_message = error.get("message")
            error_code = error.get("code")
            error_status = error.get("status")

            # If invalid request by validation error, there will be additional error information in "exc" field of the error.
            if error_code == 3 and "exc" in error:
                error_message = f"{error_message} Additional exception information: {error.get('exc')}"

            # Raise ApiError exception.
            message = f"Failed to call API method {method_name}! Error code: {error_code}. Error message: {error_message}"
            raise GateyApiError(
                message=message,
                error_code=error_code,
                error_message=error_message,
                error_status=error_status,
                response=response,
            )
