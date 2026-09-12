# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Point embeddings for the quadric spaces.

2D: ``embed_point(basis, x, y)``
    ``x b₁ + y b₂ + (√2/2) b₃ + (√2/2)x² b₄ + (√2/2)y² b₅ + x y b₆``

3D: ``embed_point(basis, x, y, z)``
    ``x b₁ + y b₂ + z b₃ + (√2/2) b₄ + (√2/2)x² b₅ + (√2/2)y² b₆
    + (√2/2)z² b₇ + x y b₈ + x z b₉ + y z b₁₀``
"""

from __future__ import annotations

import numpy as np

from pytanga.algebra._mv import MV

_SQRT2_OVER_2 = float(np.sqrt(2.0) / 2.0)


def embed_point(basis, x: float, y: float | None = None, z: float | None = None) -> MV:
    """Embed a point into the quadric space as a rank-1 grade-1 blade.

    ``embed_point`` is the Euclidean-rescaled ``D_op(x) = x xᵀ``: its inner
    product with ``coeff(A)`` equals ``½ xᵀ A x`` (see the package README).
    """
    dim = basis.dim
    if dim == 6:
        if y is None or z is not None:
            raise ValueError(
                "2D embed_point(basis, x, y) takes exactly two coordinates"
            )
        return basis.multivector(
            {
                1: x,
                2: y,
                4: _SQRT2_OVER_2,
                8: _SQRT2_OVER_2 * x * x,
                16: _SQRT2_OVER_2 * y * y,
                32: x * y,
            }
        )
    if dim == 10:
        if y is None or z is None:
            raise ValueError(
                "3D embed_point(basis, x, y, z) takes exactly three coordinates"
            )
        return basis.multivector(
            {
                1: x,
                2: y,
                4: z,
                8: _SQRT2_OVER_2,
                16: _SQRT2_OVER_2 * x * x,
                32: _SQRT2_OVER_2 * y * y,
                64: _SQRT2_OVER_2 * z * z,
                128: x * y,
                256: x * z,
                512: y * z,
            }
        )
    raise ValueError(f"unsupported quadric basis dimension: {dim}")
