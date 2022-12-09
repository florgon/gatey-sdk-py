"""
    Utils stuff.
"""

import sys
import platform

from typing import Any, Dict

from gatey_sdk.consts import SDK_INFORMATION_DICT
from gatey_sdk.consts import (
    RUNTIME_NAME,
)


def remove_trailing_slash(url: str) -> str:
    """
    Removes trailing slash from a URL.
    Example: `http://example.com/` will become `http://example.com` (No trailing slash)

    :param url: The URL to remove trailing slash.
    """
    if not isinstance(url, str):
        raise TypeError("URL must be a string!")

    if url.endswith("/"):
        url = url[:-1]

    return url


def get_additional_event_tags(
    include_platform_info: bool = True,
    include_runtime_info: bool = True,
    include_sdk_info: bool = True,
) -> Dict[str, Any]:
    """
    Returns additional event dictionary for tags with event information such as SDK information, platform information etc.
    """
    additional_event_tags = dict()
    if include_sdk_info:
        additional_event_tags.update(SDK_INFORMATION_DICT)
    if include_platform_info:
        additional_event_tags.update(get_platform_event_tags())
    if include_runtime_info:
        additional_event_tags.update(get_runtime_event_tags())
    return additional_event_tags


def get_platform_event_tags() -> Dict[str, Any]:
    """
    Returns platform information for event data tags.
    """

    platform_os = platform.system()
    platform_network_name = platform.node()
    platform_event_data_tags = {
        "os": platform_os,
        "os.node": platform_network_name,
        "os.version": platform.version(),  # For major there is `platform.release()`
        "os.bits": platform.architecture()[0],
    }

    return platform_event_data_tags


def get_runtime_event_tags() -> Dict:
    """
    Returns runtime information event data tags.
    """
    runtime_name = RUNTIME_NAME
    runtime_version = sys.version_info
    runtime_version = f"{runtime_version[0]}.{runtime_version[1]}.{runtime_version[2]}-{runtime_version[3]}-{runtime_version[4]}"
    return {
        "runtime.name": runtime_name,
        "runtime.ver": runtime_version,
        "runtime.impl": platform.python_implementation(),
    }
