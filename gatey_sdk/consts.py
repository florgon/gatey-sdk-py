"""
    Constants for the SDK.
"""

from gatey_sdk.__version__ import __version__ as library_version

# Default API server provider.
# By default, this is API server provided from Florgon,
# but user can override this with self-hosted provider.
API_DEFAULT_SERVER_PROVIDER_URL = "https://api-gatey.florgon.space/v1"

# Expected version from the API server.
API_DEFAULT_SERVER_EXPECTED_VERSION = "0.0.0"

# SDK fields.
SDK_NAME = "gatey.python.official"
SDK_VERSION = library_version
SDK_INFORMATION_DICT = {"sdk.name": SDK_NAME, "sdk.ver": SDK_VERSION}

# Exception attribute names.
EXC_ATTR_SHOULD_SKIP_SYSTEM_HOOK = "gatey_should_skip_system_hook"
EXC_ATTR_WAS_HANDLED = "gatey_was_handled"
EXC_ATTR_IS_INTERNAL = "gatey_is_internal"

# Runtime name for runtime event data.
RUNTIME_NAME = "Python"

# Events buffer defaults.
DEFAULT_EVENTS_BUFFER_FLUSH_EVERY = 10.0
EVENTS_BUFFER_FLUSHER_THREAD_NAME = "gatey_sdk.events_buffer.flusher"
