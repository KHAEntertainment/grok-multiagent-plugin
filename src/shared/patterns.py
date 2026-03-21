"""
Shared regex patterns used by both grok_bridge.py and grok_agent.py.

Centralizing these patterns ensures consistent parsing across all modules.
"""

# Canonical list of supported file extensions for filename detection.
SUPPORTED_EXTENSIONS = (
    "py|js|ts|jsx|tsx|go|rs|java|c|cpp|h|hpp|cs|rb|php|swift|kt|scala|sh|bash"
)

# Regex pattern string that matches a comment-style filename header, e.g.:
#   # filename.py
_FILENAME_PATTERN_STRING = (
    r"^\s*#\s*([a-zA-Z_][a-zA-Z0-9_]*\.(?:"
    + SUPPORTED_EXTENSIONS
    + r"))\s*$"
)


def get_filename_pattern_string() -> str:
    """Return the canonical regex string for matching comment-style filename headers.

    Both grok_bridge.py and grok_agent.py compile this string (with re.MULTILINE)
    so that any change to the supported extension list is automatically reflected
    in every consumer.
    """
    return _FILENAME_PATTERN_STRING
