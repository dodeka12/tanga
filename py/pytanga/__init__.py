# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Public Python API for TANGA geometric algebra."""

from .algebra import MV, Algebra, EInv, EProduct, random_mask
from .blade_mask import BladeMask
from .codegen import precompile
from .expression import AffineExpression, DataArray, Expression, Variable
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
from .install_examples import install_examples
from .matrix import MVMatrix, MVProductMatrix
from .tensor import MVTensor

__all__ = [
    "AffineExpression",
    "Algebra",
    "BladeMask",
    "install_docs",
    "install_examples",
    "Circle",
    "DataArray",
    "Direction",
    "EInv",
    "EProduct",
    "Expression",
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
    "Variable",
    "precompile",
    "random_mask",
]
