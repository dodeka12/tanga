# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Corner anchor positions for overlays and fixed control panels."""

from __future__ import annotations

from enum import StrEnum


class EAnchor(StrEnum):
    """Anchor positions for overlays and fixed-position control panels.

    Used by the ``position`` argument of ``GroupView`` / ``MenuView`` /
    ``ControlGroup`` (and their ``add_*`` conveniences) to anchor an overlay or
    panel to its container — the viewport for global overlays, or a scene pane
    for per-pane overlays.  Corner anchors pin a corner; the edge anchors
    (``TOP`` / ``BOTTOM`` / ``LEFT`` / ``RIGHT``) center the element along that
    edge.
    """

    TOP_LEFT = "top-left"
    TOP_RIGHT = "top-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_RIGHT = "bottom-right"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
