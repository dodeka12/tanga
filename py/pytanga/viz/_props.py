# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Color normalisation utility for the Tanga 3D viewer."""

from __future__ import annotations


def _normalize_color(
    color: str | tuple[float, float, float] | tuple[float, float, float, float],
) -> str | tuple[str, float]:
    """Convert a color value to hex, extracting opacity from 4-tuples.

    Returns:
        - Hex string for str input or RGB 3-tuples.
        - ``(hex_str, opacity)`` for RGBA 4-tuples.
    """
    if isinstance(color, str):
        return color
    if isinstance(color, tuple):
        if len(color) == 3:
            r, g, b = color
            a = None
        elif len(color) == 4:
            r, g, b, a = color
        else:
            raise ValueError(f"Color tuple must have 3 or 4 elements, got {len(color)}")
        r_byte = max(0, min(255, round(r * 255)))
        g_byte = max(0, min(255, round(g * 255)))
        b_byte = max(0, min(255, round(b * 255)))
        hex_str = f"#{r_byte:02x}{g_byte:02x}{b_byte:02x}"
        if a is not None:
            return (hex_str, a)
        return hex_str
    raise TypeError(f"Color must be str or tuple, got {type(color).__name__}")
