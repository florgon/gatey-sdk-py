import requests
import time
from gatey_sdk.consts import DEFAULT_API_PROVIDER_URL


class Client:
    """
    Florgon Gatey Client.
    WIP. TBD.
    """

    _api_server_provider_url = DEFAULT_API_PROVIDER_URL

    def __init__(self, *args, **kwargs):
        self._api_server_provider_url = DEFAULT_API_PROVIDER_URL

    def method(self, name: str, **kwargs) -> any:
        url = f"{self._api_server_provider_url}/{name}"
        params = kwargs
        request = requests.get(url=url, params=params)
        return request.json()

    def change_api_provider(self, provider_url: str) -> None:
        """
        Updates API server provider URL.
        Used for selfhosted servers.
        """
        self._api_server_provider_url = provider_url

    def get_server_time_difference(self) -> int:
        client_time = time.time()
        server_time = (
            self.method("utils.getServerTime").get("success").get("server_time")
        )
        return server_time - client_time
