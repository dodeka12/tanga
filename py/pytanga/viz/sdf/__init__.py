# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Signed-distance-function viewer internals.

This package holds the Python-side pieces of the SDF viewer: the analytic
entity serializer (Phase 4), the algebra embedding (Phase 7), the
distance-function registry (Phase 3), and — since Phase 06b — the fundamental
primitive object library plus the :class:`Composed` drawable-object layer. The
frontend assets live alongside under ``templates/sdf/``.
"""

from __future__ import annotations

from .composed import Composed
from .distance import DistanceFunction, DistanceFunctionMeta
from .primitives import (
    SdfNode,
    bound_box,
    box,
    capsule,
    capped_cone,
    capped_cylinder,
    combine,
    cone,
    cylinder,
    ellipsoid,
    group,
    plane,
    primitive,
    round_box,
    segment,
    sphere,
    torus,
)
from .serializer import serialize_entity
from .visualizer import SdfVisualizer

__all__ = [
    "Composed",
    "DistanceFunction",
    "DistanceFunctionMeta",
    "SdfNode",
    "SdfVisualizer",
    "bound_box",
    "box",
    "capsule",
    "capped_cone",
    "capped_cylinder",
    "combine",
    "cone",
    "cylinder",
    "ellipsoid",
    "group",
    "plane",
    "primitive",
    "round_box",
    "segment",
    "serialize_entity",
    "sphere",
    "torus",
]
