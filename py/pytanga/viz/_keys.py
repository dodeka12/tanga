# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""General keyboard modifier declarations shared with the frontend.

These enums are the single source of truth for keyboard modifiers sent to
and received from the browser.  They are kept general so they can be reused
by both the animation-stop binding and object-interaction code.
"""

from __future__ import annotations

from enum import Enum


class KeyModifier(str, Enum):
    """Keyboard modifier keys recognized by the browser frontend.

    Members are string values so they serialize directly to JSON (via their
    ``.value``) and can be compared case-insensitively against the string
    form a user passes in.
    """

    CTRL = "ctrl"
    SHIFT = "shift"
    ALT = "alt"
    META = "meta"