# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""fit_conic_quadric.py — fit a conic/quadric from points with the GA primitives.

Fits a conic (5 points) and a quadric (9 points) two ways, both with the raw
quadric-space machinery:

1. *Join/dual* — embed each point, take the outer product of the point embeddings
   (the join), then undualize to the grade-1 conic/quadric blade.
2. *Expression system* — a grade-1 variable for the conic/quadric, bound against a
   ``DataArray`` of the embedded points through the incidence ``c.sp(p) = 0``,
   solved with ``lstsq`` / ``svd``.

The singular spectrum (from ``svd``) exposes whether the fit is well-posed
(nullity 1) or underdetermined (nullity >= 2, e.g. an apex + one coplanar circle).

``conic_from_points`` / ``quadric_from_points`` (join/dual) and
``conic_from_points_svd`` / ``quadric_from_points_svd`` / ``fit_singular_values``
/ ``fit_nullity`` are thin convenience wrappers over exactly these primitives.

Run with:  uv run python py/examples/ga/quadric/fit_conic_quadric.py

Keywords: quadric, conic, fitting, outer product, SVD, nullity
"""

import math

from pytanga.algebra import MV
from pytanga.blade_mask import BladeMask
from pytanga.expression import DataArray, Variable
from pytanga.geometry import Geometry, Point
from pytanga.quadric import BasisQ2, BasisQ3


def _coeffs1(mv: MV, dim: int) -> list[float]:
    """Read a grade-1 blade's coefficients in b1…bN order."""
    return [float(mv[1 << i]) for i in range(dim)]


def _nullity(values: list[float], tol: float) -> int:
    """Number of singular values at or below ``tol * sigma_max``."""
    scale = max(values)
    return sum(1 for v in values if abs(v) <= tol * scale)


def _main() -> None:
    q2 = BasisQ2()
    geo2 = Geometry(q2)
    conic_pts = [
        (2.0, 0.0),
        (0.0, 1.0),
        (-2.0, 0.0),
        (0.0, -1.0),
        (1.0, math.sqrt(3.0) / 2.0),
    ]

    # (1) Join/dual — outer product of the point embeddings, then undualize.
    emb = [geo2(Point(x, y, 0)) for x, y in conic_pts]
    join = emb[0] ^ emb[1] ^ emb[2] ^ emb[3] ^ emb[4]  # grade-5
    conic = join.undual()  # grade-1 conic blade

    # (2) Expression system — null space of the incidence c.sp(p) = 0.
    mask = BladeMask(q2, grades=[1])
    c = Variable("c", mask)
    pnt = Variable("p", mask)
    partial = c.sp(pnt)(p=DataArray(emb, masks=("pnt_idx", mask)))
    values, _ = partial.svd()
    conic2 = partial.lstsq()

    print("2D conic (ellipse):")
    print("  join/dual coeffs:        ", [round(v, 6) for v in _coeffs1(conic, 6)])
    print("  expression-system coeffs:", [round(v, 6) for v in _coeffs1(conic2, 6)])
    print("  singular values:         ", [round(v, 6) for v in values])
    print("  nullity (1 = well-posed):", _nullity(values, q2.precision))

    # 3D: the unit sphere through nine points.
    q3 = BasisQ3()
    geo3 = Geometry(q3)
    s = 1.0 / math.sqrt(2.0)
    t = 1.0 / math.sqrt(3.0)
    quadric_pts = [
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
        (-1.0, 0.0, 0.0),
        (0.0, -1.0, 0.0),
        (0.0, 0.0, -1.0),
        (t, t, t),
        (-t, t, -t),
        (s, -s, 0.0),
    ]
    emb3 = [geo3(Point(x, y, z)) for x, y, z in quadric_pts]
    join3 = emb3[0]
    for m in emb3[1:]:
        join3 = join3 ^ m
    quadric = join3.undual()  # grade-1 quadric blade

    mask3 = BladeMask(q3, grades=[1])
    c3 = Variable("c", mask3)
    pnt3 = Variable("p", mask3)
    partial3 = c3.sp(pnt3)(p=DataArray(emb3, masks=("pnt_idx", mask3)))
    values3, _ = partial3.svd()

    print("3D quadric (sphere):")
    print("  join/dual coeffs:", [round(v, 6) for v in _coeffs1(quadric, 10)])
    print("  nullity (1 = well-posed):", _nullity(values3, q3.precision))

    # Degenerate: an apex plus a densely-sampled *coplanar* circle only spans ~7 of
    # the 10 quadric dimensions, so the fit is underdetermined (nullity >= 2) rather
    # than a silent arbitrary member of a solution family.
    degenerate = [(0.0, 0.0, 0.0)] + [
        (math.cos(theta), math.sin(theta), 1.0)
        for theta in (2.0 * math.pi * i / 20.0 for i in range(20))
    ]
    dpts = [geo3(Point(x, y, z)) for x, y, z in degenerate]
    partial_d = c3.sp(pnt3)(p=DataArray(dpts, masks=("pnt_idx", mask3)))
    values_d, _ = partial_d.svd()
    print("coplanar degenerate fit (nullity should be >= 2):", _nullity(values_d, q3.precision))


if __name__ == "__main__":
    _main()
