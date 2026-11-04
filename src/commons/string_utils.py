"""
string_utils.py

Shared string utilities for GHFS projects.
"""

from typing import Any


def is_valid(value: Any) -> bool:
    """
    Check whether a value is a non-empty string.
    """
    return isinstance(value, str) and len(value) > 0


def default_if_empty(value: str | None, default: str) -> str:
    """
    Return a stripped string, or default when value is None/blank/"None".
    """
    if value is None:
        return default

    stripped = value.strip()
    if not stripped or stripped.lower() == "none":
        return default

    return stripped


def contains_ignoring_case(haystack: str | None, needle: str) -> bool:
    """
    Check if haystack contains needle, ignoring case.

    Returns False if haystack is None or empty.
    """
    if not haystack:
        return False
    return needle.lower() in haystack.lower()
