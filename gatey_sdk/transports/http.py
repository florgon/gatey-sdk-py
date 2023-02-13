"""
    HTTP Transport. Sends event to the Gatey Server when event sends.
"""
import json
from typing import Optional, Dict
from gatey_sdk.transports.base import BaseTransport
from gatey_sdk.api import Api
from gatey_sdk.auth import Auth
from gatey_sdk.exceptions import (
    GateyTransportImproperlyConfiguredError,
)


class HttpTransport(BaseTransport):
    """
    HTTP Transport. Sends event to the Gatey Server when event sends.
    """

    # Allowed aggreation / composition..
    _api_provider: Api = None
    _auth_provider: Optional[Auth] = None

    def __init__(self, api: Optional[Api] = None, auth: Optional[Auth] = None):
        """
        :param api: Api provider.
        :param auth: Authentication provider.
        """

        BaseTransport.__init__(self)
        self._auth_provider = auth if auth else Auth()
        self._api_provider = api if api else Api(self._auth_provider)
        self._check_improperly_configured()

    @BaseTransport.transport_base_sender_wrapper
    def send_event(self, event_dict: Dict) -> None:
        """
        Sends event to the Gatey API server.
        """
        api_params = self._api_params_from_event_dict(event_dict=event_dict)
        self._api_provider.method("event.capture", send_project_auth=True, **api_params)

    @staticmethod
    def _api_params_from_event_dict(event_dict: Dict[str, str]) -> Dict[str, str]:
        """
        Converts event dict to ready for sending API params dict.
        """
        api_params = {
            "level": event_dict["level"],
        }

        event_params = ["exception", "message", "tags"]

        for param in event_params:
            if param in event_dict:
                api_params[param] = json.dumps(event_dict[param])

        return api_params

    def _check_improperly_configured(self):
        """
        Raises error if auth provider improperly configured for sending event.
        """
        if self._auth_provider.project_id is None:
            raise GateyTransportImproperlyConfiguredError(
                "HttpTransport improperly configured! No project id found in auth provider!"
            )
        if (
            self._auth_provider.server_secret is None
            and self._auth_provider.client_secret is None
        ):
            raise GateyTransportImproperlyConfiguredError(
                "HttpTransport improperly configured! No client / server secret found in auth provider!"
            )
