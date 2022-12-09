"""
    Package with internal modules, used at core sdk level.

    Provides modules for working with traceback, source code fetching, exceptions at level of sdk (low-level).

    Should not be used by not sdk, as it is not designed to be used from elsewhere.
"""

from gatey_sdk.internal.traceback import (
    get_trace_from_traceback,
    get_variables_from_traceback,
)
from gatey_sdk.internal.source import get_context_lines_from_source_code
from gatey_sdk.internal.exc import (
    wrap_in_exception_handler,
    register_system_exception_hook,
    event_dict_from_exception,
)

__all__ = [
    "get_trace_from_traceback",
    "get_variables_from_traceback",
    "get_context_lines_from_source_code",
    "wrap_in_exception_handler",
    "register_system_exception_hook",
    "event_dict_from_exception",
]
