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

from .algebra_embedding import algebra_name, embed_entity_mv, embed_src
from .composed import Composed
from .distance import DistanceFunction, DistanceFunctionMeta
from .lights import DirectionalLight, Light
from .overlay import Axes, Grid, SdfOverlay
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
from .serializer import serialize_entity, serialize_mv
from .visualizer import SdfVisualizer

__all__ = [
    "Axes",
    "Composed",
    "DirectionalLight",
    "DistanceFunction",
    "DistanceFunctionMeta",
    "Grid",
    "Light",
    "SdfNode",
    "SdfOverlay",
    "SdfVisualizer",
    "algebra_name",
    "bound_box",
    "box",
    "capsule",
    "capped_cone",
    "capped_cylinder",
    "combine",
    "cone",
    "cylinder",
    "ellipsoid",
    "embed_entity_mv",
    "embed_src",
    "group",
    "plane",
    "primitive",
    "round_box",
    "segment",
    "serialize_entity",
    "serialize_mv",
    "sphere",
    "torus",
]
