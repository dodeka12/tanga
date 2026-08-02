# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Public Python API for TANGA geometric algebra."""

from .algebra import MV, Algebra, EInv, EProduct, random_mask, random_mv
from .blade_mask import BladeMask
from .codegen import precompile
from .geometry import (
    Circle,
    Direction,
    Line,
    Plane,
    Point,
    PointPair,
    Space,
    Sphere,
)
from .install_docs import install_docs
from .matrix import MVMatrix, MVProductMatrix
from .tensor import MVTensor

__all__ = [
    "Algebra",
    "BladeMask",
    "install_docs",
    "Circle",
    "Direction",
    "EInv",
    "EProduct",
    "Line",
    "MVMatrix",
    "MVProductMatrix",
    "MVTensor",
    "MV",
    "Plane",
    "Point",
    "PointPair",
    "Space",
    "Sphere",
    "precompile",
    "random_mask",
    "random_mv",
]
