#!/usr/bin/env python3
"""
patterns.py — Shared regex patterns for parsing Grok response code blocks.

Used by grok_bridge.py and grok_agent.py to identify file annotations inside
fenced code blocks in Grok's markdown output.
"""


def get_filename_pattern_string():
    """
    Return a regex string matching '# filename.ext' as the first line of a
    code block — a common Grok output pattern when no explicit FILE: marker
    is present.

    Pattern matches lines like:
        # task.py
        # utils/helpers.js
        # README.md

    Does NOT match:
        # /absolute/path/file.py  (use file_marker_pattern for those)
        # some comment without extension
        # FILE: path  (handled by file_marker_pattern)

    Group 1 captures the filename (possibly with a relative subdirectory).
    """
    return r'^#\s+([^\s/][^\s]*\.[a-zA-Z0-9]+)\s*$'
