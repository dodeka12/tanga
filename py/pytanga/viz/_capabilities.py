# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Renderer capability map — which entity kinds support which renderers.

The serializer consults this table so that an unsupported entity/renderer
combination raises a clear error instead of emitting a wire object the
frontend cannot draw.
"""

from __future__ import annotations

#: Entity kinds that support the analytic ``"ray"`` renderer.  Everything else
#: keeps the standard ``"mesh"`` / ``"sdf"`` paths.
_RAY_CAPABLE_KINDS: frozenset[str] = frozenset({"Quadric3D"})

#: Default renderer kinds for a kind not listed in the capability table.
_DEFAULT_RENDERERS: frozenset[str] = frozenset({"mesh", "sdf"})


def _supports_renderer(kind: str, renderer: str) -> bool:
    """Return ``True`` when *kind* can be drawn with *renderer*."""
    if renderer == "ray":
        return kind in _RAY_CAPABLE_KINDS
    if kind in _RAY_CAPABLE_KINDS:
        # A ray-only kind has no mesh/sdf fallback.
        return False
    return renderer in _DEFAULT_RENDERERS
