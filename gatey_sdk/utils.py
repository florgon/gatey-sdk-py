"""
    Utils methods.
"""
from typing import Dict, List, Callable, Optional
from types import TracebackType


def wrap_in_exception_handler(
    *,
    reraise: bool = True,
    exception: BaseException | None = None,
    ignored_exceptions: list[BaseException] | None = None,
    on_catch_exception: Optional[Callable] = None,
) -> Callable:
    """
    Decorator that catches the exception and captures it as Gatey exception.
    :param reraise: If False, will not raise the exception again, application will not fall (WARNING: USE THIS WISELY TO NOT GET UNEXPECTED BEHAVIOR)
    :param exception: Target exception type to capture.
    :param ignored_exceptions: List of exceptions that should not be captured.
    :param on_catch_exception: Function that will be called when an exception is caught.
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

                # Do not handle ignored exceptions.
                if exception_is_ignored(e, ignored_exceptions):
                    raise e

                # Call catch event.
                if callable(on_catch_exception):
                    on_catch_exception(e)

                # Raise exception again if we expected that.
                if reraise is True:
                    raise e

        return wrapper

    return decorator


def exception_is_ignored(
    exception: BaseException, ignored_exceptions: list[BaseException]
) -> bool:
    """
    Returns True if exception should be ignored based on `ignored_exceptions` list.
    """
    exception_type = type(exception)
    for ignored_exception_type in ignored_exceptions:
        if exception_type == ignored_exception_type:
            return True
    return False


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


def get_variables_from_traceback(traceback: TracebackType) -> Dict:
    """
    Returns local and global variables from the given traceback.
    """

    traceback_variables_locals = traceback.tb_frame.f_locals
    traceback_variables_globals = traceback.tb_frame.f_globals

    return {
        "locals": traceback_variables_locals,
        "globals": traceback_variables_globals,
    }
