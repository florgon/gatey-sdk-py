"""
    Utils methods.
"""

import sys
import platform

from typing import Dict, List, Callable, Optional
from types import TracebackType

from gatey_sdk.consts import SDK_INFORMATION_DICT
from gatey_sdk.exceptions import GateyApiError, GateyTransportError
from gatey_sdk.consts import (
    EXC_ATTR_SHOULD_SKIP_SYSTEM_HOOK,
    EXC_ATTR_WAS_HANDLED,
    RUNTIME_NAME,
)


def wrap_in_exception_handler(
    *,
    reraise: bool = True,
    exception: BaseException | None = None,
    ignored_exceptions: List[BaseException] | None = None,
    on_catch_exception: Optional[Callable] = None,
    skip_global_handler_on_ignore: bool = False,
) -> Callable:
    """
    Decorator that catches the exception and captures it as Gatey exception.
    :param reraise: If False, will not raise the exception again, application will not fall (WARNING: USE THIS WISELY TO NOT GET UNEXPECTED BEHAVIOR)
    :param exception: Target exception type to capture.
    :param ignored_exceptions: List of exceptions that should not be captured.
    :param on_catch_exception: Function that will be called when an exception is caught.
    :param skip_global_handler_on_ignore: If true, will skip global exception handler if exception was ignored.
    """

    # Default target exception value.
    if exception is None:
        exception = BaseException

    # Default value for ignored exception list (Do not ignore any exceptions)
    if ignored_exceptions is None:
        ignored_exceptions = []

    def decorator(function: Callable):
        def wrapper(*args, **kwargs):
            # Gets called when `decorated` function get called.
            try:
                # This will simply return function result if there is no exception.
                return function(*args, **kwargs)
            except exception as e:
                # There is any exception that we should handle occurred.

                # Typed.
                e: BaseException = e

                if skip_global_handler_on_ignore:
                    # If we should skip global exception handler.
                    setattr(e, EXC_ATTR_SHOULD_SKIP_SYSTEM_HOOK, True)

                # Do not handle ignored exceptions.
                if exception_is_ignored(e, ignored_exceptions):
                    raise e

                # Call catch event.
                if callable(on_catch_exception):
                    on_catch_exception(e)

                # Mark as handled.
                setattr(e, EXC_ATTR_WAS_HANDLED, True)

                # Raise exception again if we expected that.
                if reraise is True:
                    raise e

        return wrapper

    return decorator


def register_system_exception_hook(hook: Callable):
    """
    Register exception hook for system.
    :param hook: Will be called when exception triggered.
    """

    def _system_exception_hook_handler(
        exception_type: type[BaseException],
        exception: BaseException,
        traceback: TracebackType,
    ):
        # System exception hook handler.

        if not hasattr(exception, EXC_ATTR_SHOULD_SKIP_SYSTEM_HOOK):
            # If marked as skipped for system hook.
            try:
                # Try to handle this exception with hook.
                hook(exception=exception)
                return
            except (GateyApiError, GateyTransportError):
                # If there is any error while processing global exception handler.
                pass

        # Default system hook.
        sys.__excepthook__(exception_type, exception, traceback)

    # Register system exception hook.
    sys.excepthook = _system_exception_hook_handler


def exception_is_ignored(
    exception: BaseException, ignored_exceptions: List[BaseException]
) -> bool:
    """
    Returns True if exception should be ignored based on `ignored_exceptions` list.
    """
    exception_type = type(exception)
    for ignored_exception_type in ignored_exceptions:
        if exception_type == ignored_exception_type:
            return True
    return False


def event_dict_from_exception(exception: BaseException, skip_vars: bool = True) -> Dict:
    """
    Returns event dictionary of the event (field) from the raw exception.
    Fetches all required information about system, exception.
    """

    # Get raw exception traceback information.
    exception_traceback = getattr(exception, "__traceback__", None)

    # Query traceback information.
    traceback_vars = get_variables_from_traceback(
        traceback=exception_traceback, _always_skip=skip_vars
    )
    traceback_trace = get_trace_from_traceback(exception_traceback)

    # Get exception type ("BaseException", "ValueError").
    exception_type = get_exception_type_name(exception)
    exception_description = str(exception)
    event_dict = {
        "class": exception_type,
        "description": exception_description,
        "vars": traceback_vars,
        "traceback": traceback_trace,
    }
    return event_dict


def get_exception_type_name(exception: BaseException) -> str:
    """
    Returns exception type ("BaseException", "ValueError").
    """
    return getattr(type(exception), "__name__", "NoneException")


def get_additional_event_data() -> Dict:
    """
    Returns additional event dictionary with event information such as SDK information, platform information etc.
    """
    sdk_information = SDK_INFORMATION_DICT
    platform_information = get_platform_event_data()
    runtime_information = get_runtime_event_data()
    additional_event_data = {
        "sdk": sdk_information,
        "platform": platform_information,
        "runtime": runtime_information,
    }
    return additional_event_data


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


def get_trace_from_traceback(traceback: TracebackType) -> List[Dict]:
    """
    Returns trace from the given traceback.
    """

    trace = []

    while traceback is not None:
        # Iterating over traceback with `tb_next`
        trace_element = {
            "filename": traceback.tb_frame.f_code.co_filename,
            "name": traceback.tb_frame.f_code.co_name,
            "line": traceback.tb_lineno,
        }
        trace.append(trace_element)
        traceback = traceback.tb_next

    return trace


def get_platform_event_data() -> Dict:
    """
    Returns platform information for event data.
    """
    platform_os = platform.system()
    platform_network_name = platform.node()
    platform_event_data = {
        "os": platform_os,
        "node": platform_network_name,
        "version": platform.version(),  # For major there is `platform.release()`
        "arch": {
            "bits": platform.architecture()[0],
            "linkage": platform.architecture()[1],
        },
        "processor": platform.processor(),
        "machine": platform.machine(),
        "platform": platform.platform(terse=False),
    }
    if platform_os == "Windows":
        # This is only for Windows.
        # (but there is also more same specific stuff for other operating system).
        # Also this is for now will not be handled by API.
        platform_event_data.update(
            {
                "os.win32.ver": platform.win32_ver(),
                "os.win32.edition": platform.win32_edition(),
                "os.win32.is_iot": platform.win32_is_iot(),
            }
        )

    return platform_event_data


def get_runtime_event_data() -> Dict:
    """
    Returns runtime information for event data.
    """
    runtime_name = RUNTIME_NAME
    runtime_version = sys.version_info
    runtime_version = f"{runtime_version[0]}.{runtime_version[1]}.{runtime_version[2]}-{runtime_version[3]}-{runtime_version[4]}"
    runtime_build = platform.python_build()
    runtime_build = f"{runtime_build[0]}.{runtime_build[1]}"
    return {
        "name": runtime_name,
        "version": runtime_version,
        "build": runtime_build,
        "compiler": platform.python_compiler(),
        "branch": platform.python_branch(),
        "implementation": platform.python_implementation(),
        "revision": platform.python_revision(),
    }


def get_variables_from_traceback(
    traceback: TracebackType, *, _always_skip: bool = False
) -> Dict:
    """
    Returns local and global variables from the given traceback.
    """

    traceback_variables_locals = {}
    traceback_variables_globals = {}

    if traceback and not _always_skip:
        traceback_variables_locals = traceback.tb_frame.f_locals
        traceback_variables_globals = traceback.tb_frame.f_globals

    # Stringify variable values.
    traceback_variables_locals = {
        key: str(value) for key, value in traceback_variables_locals.items()
    }
    traceback_variables_globals = {
        key: str(value) for key, value in traceback_variables_globals.items()
    }

    return {
        "locals": traceback_variables_locals,
        "globals": traceback_variables_globals,
    }
