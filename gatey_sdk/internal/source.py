"""
    Works with source code reading.
"""

import tokenize
from typing import Dict, List, Union


def get_context_lines_from_source_code(
    filename: str, line_number: int, context_lines_count: int = 5
) -> Dict[str, Union[str, None, List[str]]]:
    """
    Returns context lines from source code file.
    """
    source_code_lines = _get_lines_from_source_code(filename=filename)
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


def _get_lines_from_source_code(filename: str) -> List[str]:
    """
    Returns lines of the code from the source code filename.
    """
    try:
        with tokenize.open(filename=filename) as source_file:
            return source_file.readlines()
    except (OSError, IOError):
        return []
