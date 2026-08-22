# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Signed-distance-function viewer internals.

This package holds the Python-side pieces of the SDF viewer: the analytics
entity serializer (Phase 4), the algebra embedding (Phase 7), and the
distance-function registry (Phase 3). The frontend assets live alongside under
``templates/sdf/``.
"""

from __future__ import annotations

from .distance import DistanceFunction, DistanceFunctionMeta

__all__ = ["DistanceFunction", "DistanceFunctionMeta"]