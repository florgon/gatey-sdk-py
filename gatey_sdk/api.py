"""
    API class for working with API (HTTP).
    Sends HTTP requests, handles API methods.
"""
from typing import Optional, Dict, Any

import requests

from gatey_sdk.auth import Auth
from gatey_sdk.response import Response
from gatey_sdk.exceptions import GateyApiError, GateyApiAuthError, GateyApiResponseError
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

    # Timeout for requests.
    _api_server_requests_timeout = 7

    # Version that expected from the API.
    _api_server_expected_version = API_DEFAULT_SERVER_EXPECTED_VERSION

    # `Auth` instance that provides authentication fields.
    _auth_provider: Auth = None

    # Kwargs for HTTP request call.
    _http_request_kwargs: Dict[str, Any] = dict()

    def __init__(
        self,
        auth: Optional[Auth] = None,
        *,
        http_request_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        :param auth: Auth provider as the `Auth` instance.
        :param http_request_kwargs: Kwargs that will be passed to the HTTP requests call.
        """
        if auth and not isinstance(auth, Auth):
            raise TypeError(
                "Auth must be an instance of `Auth`! You may not pass auth as it will be initialise blank internally in `Api`."
            )
        self._auth_provider = auth if auth else Auth()
        self._http_request_kwargs = http_request_kwargs

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

        # Build URL where API method is located.
        api_server_method_url = f"{self._api_server_provider_url}/{name}"

        # Send HTTP request.
        http_response = requests.get(
            url=api_server_method_url,
            params=http_params,
            timeout=self._api_server_requests_timeout,
            **self._http_request_kwargs,
        )

        # Wrap HTTP response in to own Response object.
        try:
            response = Response(http_response=http_response)
        except requests.exceptions.JSONDecodeError:
            raise GateyApiResponseError(
                f"Failed to parse JSON response for response wrapper (Mostly due to server-side error!). Status code: {http_response.status_code}",
                raw_response=http_response,
            )

        # Raise exception if there is any error returned with Api.
        self._process_error_and_raise(
            method_name=name, response=response, raw_response=http_response
        )

        return response

    def change_api_server_provider_url(self, provider_url: str) -> None:
        """
        Updates API server provider URL.
        Used for self-hosted servers.
        :param provider_url: URL of the server API provider.
        """
        provider_url = remove_trailing_slash(provider_url)
        self._api_server_provider_url = provider_url

    def change_api_server_timeout(self, timeout: int) -> None:
        """
        Updates API timeout for requests.
        :param timeout: New timeout
        """
        self._api_server_requests_timeout = timeout

    def change_api_server_expected_version(self, version: str) -> None:
        """
        Updates API version.
        :param version: Version of API.
        """
        self._api_server_expected_version = version

    def do_auth_check(self) -> bool:
        """
        Checks authentication with API.
        Returns is it successfully or no.
        """
        try:
            self.do_hard_auth_check()
        except (GateyApiError, GateyApiAuthError):
            return False
        return True

    def do_hard_auth_check(self) -> bool:
        """
        Checks authentication with API.
        Raises API error exception if unable to authenticate you.
        """
        try:
            self.method(
                "project.checkAuthority",
                send_access_token=False,
                send_project_auth=True,
            )
        except GateyApiError as api_error:
            if api_error.error_code == 7:
                if "please use server secret" in api_error.error_message.lower():
                    # TODO: Checkout backend rework for that case.
                    raise GateyApiAuthError(
                        "Project settings restricts using client secret, please use server secret instead of client, or ask to change project settings."
                    ) from api_error
                raise GateyApiAuthError(
                    "You are entered incorrect project secret (client or server)! Please review your SDK settings! (See previous exception to see more described information)"
                ) from api_error
            if api_error.error_code == 8:
                raise GateyApiAuthError(
                    "You are entered not existing project id! Please review your SDK settings! (See previous exception to see more described information)"
                ) from api_error
            raise GateyApiAuthError(
                "There is unknown error while trying to check auth (do_auth)! (See previous exception to see more described information)"
            ) from api_error

    @staticmethod
    def _process_error_and_raise(
        method_name: str, response: Response, raw_response: requests.Response
    ) -> None:
        """
        Processes error, and if there is any error, raise ApiError exception.
        """
        error = response.raw_json().get("error")
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
                raw_response=raw_response,
            )
