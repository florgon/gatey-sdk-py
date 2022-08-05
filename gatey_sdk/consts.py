"""
    Constants for the SDK.
"""

from gatey_sdk.__version__ import __version__ as library_version

# Default API server provider.
# By default, this is API server provided from Florgon,
# but user can override this with self-hosted provider.
API_DEFAULT_SERVER_PROVIDER_URL = "https://api.florgon.space/gatey"

# Expected version from the API server.
API_DEFAULT_SERVER_EXPECTED_VERSION = "0.0.0"

# SDK fields.
SDK_NAME = "gatey.python.sdk.official"
SDK_VERSION = library_version
SDK_INFORMATION_DICT = {"name": SDK_NAME, "version": SDK_VERSION}
