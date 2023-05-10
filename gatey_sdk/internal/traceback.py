"""
    Stuff to work with tracebacks.
"""

from typing import List, Dict
from types import TracebackType, FrameType

from gatey_sdk.internal.source import get_context_lines_from_source_code


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


def get_variables_from_traceback(
    traceback: TracebackType, *, _always_skip: bool = False
) -> Dict:
    """
    Returns local and global variables from the given traceback.
    """

    traceback_variables_locals = {}
    traceback_variables_globals = {}

    if traceback and not _always_skip:
        last_frame = _traceback_query_tail_frame(traceback)
        traceback_variables_locals = last_frame.f_locals
        traceback_variables_globals = last_frame.f_globals

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


def _traceback_query_tail_frame(traceback: TracebackType) -> FrameType:
    """
    Returns last frame of the frame (tail).
    """
    tail_frame = traceback.tb_frame
    while traceback is not None:
        tail_frame = traceback.tb_frame
        traceback = traceback.tb_next
    return tail_frame
