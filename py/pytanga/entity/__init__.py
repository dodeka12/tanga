# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Fundamental, dependency-free entity primitives.

This leaf package owns the 3D vector type (:class:`Vec3`) and the semantic
``Point`` / ``Direction`` entities built on it, plus the ``Refinable`` protocol
and the MV-conversion registry.  It imports nothing from ``pytanga.geometry``
or ``pytanga.quadric`` so it can sit at the bottom of the module DAG.
"""

from ._util import _is_mv, _scalar, register_analyzer
from .base import Refinable
from .direction import Direction
from .point import Point
from .vec3 import Vec3

__all__ = [
    "Direction",
    "Point",
    "Refinable",
    "Vec3",
    "_is_mv",
    "_scalar",
    "register_analyzer",
]
