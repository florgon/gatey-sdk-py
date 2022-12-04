"""
    Utils methods.
"""

import sys
import platform
import tokenize

from typing import Any, Dict, List, Callable, Optional, Union
from types import TracebackType

from gatey_sdk.consts import SDK_INFORMATION_DICT
from gatey_sdk.exceptions import (
    GateyApiError,
    GateyTransportError,
    GateyTransportImproperlyConfiguredError,
)
from gatey_sdk.consts import (
    EXC_ATTR_SHOULD_SKIP_SYSTEM_HOOK,
    EXC_ATTR_WAS_HANDLED,
    RUNTIME_NAME,
)


def wrap_in_exception_handler(
    *,
    reraise: bool = True,
    exception: Optional[BaseException] = None,
    ignored_exceptions: Optional[List[BaseException]] = None,
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

                # Do not handle ignored exceptions.
                if exception_is_ignored(e, ignored_exceptions):
                    if skip_global_handler_on_ignore:
                        # If we should skip global exception handler.
                        setattr(e, EXC_ATTR_SHOULD_SKIP_SYSTEM_HOOK, True)
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


def register_system_exception_hook(
    hook: Callable, skip_internal_exceptions: bool = True
):
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

        was_handled = hasattr(exception, EXC_ATTR_WAS_HANDLED)
        if not was_handled and not hasattr(exception, EXC_ATTR_SHOULD_SKIP_SYSTEM_HOOK):
            # If marked as skipped for system hook.
            try:
                # Try to handle this exception with hook.
                hook(exception=exception)
            except (
                GateyApiError,
                GateyTransportError,
                GateyTransportImproperlyConfiguredError,
            ) as e:
                # If there is any error while processing global exception handler.
                if not skip_internal_exceptions:
                    raise e

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


def event_dict_from_exception(
    exception: BaseException, skip_vars: bool = True, include_code_context: bool = True
) -> Dict:
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
    traceback_trace = get_trace_from_traceback(
        exception_traceback, include_code_context=include_code_context
    )

    # Get exception type ("BaseException", "ValueError").
    exception_type = get_exception_type_name(exception)
    exception_description = str(exception)
    event_dict = {
        "class": exception_type,
        "description": exception_description,
        "vars": traceback_vars,  # Will be migrated to the traceback context later.
        "traceback": traceback_trace,
    }
    return event_dict


def get_exception_type_name(exception: BaseException) -> str:
    """
    Returns exception type ("BaseException", "ValueError").
    """
    return getattr(type(exception), "__name__", "NoneException")


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


def get_trace_from_traceback(
    traceback: TracebackType,
    include_code_context: bool = True,
    code_context_lines_count: int = 5,
    code_context_only_for_tail: bool = True,
) -> List[Dict]:
    """
    Returns trace from the given traceback.
    """

    trace = []

    while traceback is not None:
        # Iterating over traceback with `tb_next`
        frame = traceback.tb_frame
        frame_code = getattr(frame, "f_code", None)
        filename, function = None, None
        if frame_code:
            filename = frame.f_code.co_filename
            function = frame.f_code.co_name

        line_number = traceback.tb_lineno
        trace_element = {
            "filename": filename,
            "name": function or "<unknown>",
            "line": line_number,
            "module": frame.f_globals.get("__name__", None),
        }

        if include_code_context and not code_context_only_for_tail:
            trace_element |= {
                "context": get_context_lines_from_source_code(
                    filename=filename,
                    line_number=line_number,
                    context_lines_count=code_context_lines_count,
                )
            }

        trace.append(trace_element)
        traceback = traceback.tb_next

    if include_code_context and code_context_only_for_tail:
        tail_trace = trace[-1]
        tail_trace["context"] = get_context_lines_from_source_code(
            filename=tail_trace["filename"],
            line_number=tail_trace["line"],
            context_lines_count=5,
        )

    return trace


def get_context_lines_from_source_code(
    filename: str, line_number: int, context_lines_count: int = 5
) -> Dict[str, Union[str, None, List[str]]]:
    """
    Returns context lines from source code file.
    """
    source_code_lines = get_lines_from_source_code(filename=filename)
    bounds_start = max(0, line_number - context_lines_count - 1)
    bounds_end = min(line_number + 1 + context_lines_count, len(source_code_lines))

    strip_line = lambda line: line.strip("\r\n").replace("    ", "\t")
    context_pre, context_target, context_post = [], None, []
    try:
        context_pre = [
            strip_line(line)
            for line in source_code_lines[bounds_start : line_number - 1]
        ]
        context_target = strip_line(source_code_lines[line_number - 1])
        context_post = [
            strip_line(line) for line in source_code_lines[line_number:bounds_end]
        ]
    except IndexError:
        # File was changed?
        pass
    return {"pre": context_pre, "target": context_target, "post": context_post}


def get_lines_from_source_code(filename: str) -> List[str]:
    """
    Returns lines of the code from the source code filename.
    """
    try:
        with tokenize.open(filename=filename) as source_file:
            return source_file.readlines()
    except (OSError, IOError):
        return []


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
