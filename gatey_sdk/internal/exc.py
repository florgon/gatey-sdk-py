"""
    Stuff for working with exceptions on SDK level.
"""

import sys

from typing import Dict, List, Callable, Optional
from types import TracebackType

from gatey_sdk.exceptions import (
    GateyApiError,
    GateyTransportError,
    GateyTransportImproperlyConfiguredError,
)
from gatey_sdk.consts import (
    EXC_ATTR_SHOULD_SKIP_SYSTEM_HOOK,
    EXC_ATTR_WAS_HANDLED,
)
from gatey_sdk.internal.traceback import (
    get_trace_from_traceback,
    get_variables_from_traceback,
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
                if _exception_is_ignored(e, ignored_exceptions):
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
            return

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
    exception_type = _get_exception_type_name(exception)
    exception_description = str(exception)
    event_dict = {
        "class": exception_type,
        "description": exception_description,
        "vars": traceback_vars,  # Will be migrated to the traceback context later.
        "traceback": traceback_trace,
    }
    return event_dict


def _get_exception_type_name(exception: BaseException) -> str:
    """
    Returns exception type ("BaseException", "ValueError").
    """
    return getattr(type(exception), "__name__", "NoneException")


def _exception_is_ignored(
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
