import gatey_sdk
from gatey_sdk.consts import (
    API_DEFAULT_SERVER_EXPECTED_VERSION,
    API_DEFAULT_SERVER_PROVIDER_URL,
)

client = gatey_sdk.Client(
    project_id=-1, server_secret="secret", check_api_auth_on_init=False
)
client.api.change_api_server_provider_url(API_DEFAULT_SERVER_PROVIDER_URL)
client.api.change_api_server_expected_version(API_DEFAULT_SERVER_EXPECTED_VERSION)
client.api.change_api_server_timeout(5)
