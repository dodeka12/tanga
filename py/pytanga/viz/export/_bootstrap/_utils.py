# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""Utility helpers for escaping and formatting."""

from __future__ import annotations


def _escape_html(text: str) -> str:
    """Escape text for inclusion in HTML."""
    return text.replace("&", "&").replace("<", "<").replace(">", ">")


def _escape_js(s: str) -> str:
    """Escape a string for embedding in JS single-quoted string literals."""
    return (
        s.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\n", "\\n")
        .replace("\r", "")
    )


def _format_js_bool(val: bool) -> str:
    """Return 'true' or 'false' as a JS boolean literal."""
    return "true" if val else "false"


def contains_math(text: str) -> bool:
    """Return True if *text* contains LaTeX math delimiters (``$``)."""
    if not text:
        return False
    return "$" in text
