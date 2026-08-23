# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Algebra SDF backend (Phase 7): reduce an MV to a product matrix ``M``.

Given an MV ``e`` (an entity/operator blade) and a 3D point, the shader computes
the signed distance as ``r = M·a``, ``d = distOf(r)`` where ``a`` is the
algebra-specific point embedding (``evalPoint``) and ``distOf`` is the active
distance function. ``M`` is the partially-contracted product tensor: the result
blade axis is kept, the entity blade axis is contracted out on the backend, so
the shader only supplies the point.

This module is the single source of truth for the canonical blade ordering
shared between ``M`` (``result_ids`` / ``point_ids``) and the ``evalPoint`` GLSL
snippet in ``templates/sdf/algebra/embeds.js``.

Design decisions (see the Phase 7 plan and the README):

- **The point is the OPNS point, fixed per algebra** (independent of the
  entity's ``opns`` flag): ``e3`` → ``x·e1 + y·e2 + z·e3``; ``p3`` →
  ``x·e1 + y·e2 + z·e3 + e4``; ``n3`` → the conformal null-vector point
  (quadratic in ρ); ``pga3`` → the J-map dual trivector point. The entity's
  ``opns`` flag selects the *product* only: ``opns=True → op``,
  ``opns=False → ip``.
- **The result blade mask is the full algebra** (all blades, scalar at slot 0,
  pseudoscalar at the last slot), because the distance functions (e.g. the
  default ``scalar_pseudo``) read the scalar, the pseudoscalar, and the
  magnitude of every other grade.
- **``normalize=True``** (default) normalizes the MV before contraction so
  ``|r|`` is a usable sphere-tracing step size.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from pytanga.algebra import EProduct, MV
from pytanga.blade_mask import BladeMask
from pytanga.tensor import MVTensor
from pytanga.tensor.ops import contract
from pytanga.tensor.product import product_tensor


@dataclass(frozen=True)
class AlgebraSpec:
    """Per-algebra embedding spec (the point side of ``M``).

    ``point_ids`` are the canonical (ascending) blade ids of the OPNS point;
    they are the ``a[]`` coefficient slots filled by ``point_body`` (the GLSL
    ``evalPoint`` body) and the columns of ``M``.
    """

    name: str
    point_ids: tuple[int, ...]
    point_body: str
    default_bound: tuple[float, float, float] | None


_SPECS: dict[str, AlgebraSpec] = {
    "e3": AlgebraSpec(
        "e3",
        (1, 2, 4),
        """
    a[0] = p.x;
    a[1] = p.y;
    a[2] = p.z;""",
        (10.0, 10.0, 10.0),
    ),
    "p3": AlgebraSpec(
        "p3",
        (1, 2, 4, 8),
        """
    a[0] = p.x;
    a[1] = p.y;
    a[2] = p.z;
    a[3] = 1.0;""",
        (10.0, 10.0, 10.0),
    ),
    "n3": AlgebraSpec(
        "n3",
        (1, 2, 4, 8, 16),
        """
    float rho2 = dot(p, p);
    a[0] = p.x;
    a[1] = p.y;
    a[2] = p.z;
    a[3] = 0.5 * (rho2 - 1.0);
    a[4] = 0.5 * (rho2 + 1.0);""",
        (10.0, 10.0, 10.0),
    ),
    "pga3": AlgebraSpec(
        "pga3",
        (7, 11, 13, 14, 19, 21, 22),
        """
    a[0] = 1.0;
    a[1] = -p.z;
    a[2] = p.y;
    a[3] = -p.x;
    a[4] = -p.z;
    a[5] = p.y;
    a[6] = -p.x;""",
        (10.0, 10.0, 10.0),
    ),
}


def algebra_name(alg) -> str:
    """Return the canonical name (``e3|p3|n3|pga3``) for an algebra instance."""
    name = type(alg).__name__
    if name == "BasisE3":
        return "e3"
    if name == "BasisP3":
        return "p3"
    if name == "BasisN3":
        return "n3"
    if name == "BasisPGA3":
        return "pga3"
    # Bare Algebra fallback by (dim, sig).
    key = (alg.dim, alg.sig)
    if key == (3, 0):
        return "e3"
    if key == (4, 0):
        return "p3"
    if key == (5, 0b10000):
        # Raw null algebra; the plane-based interpretation needs BasisPGA3.
        return "n3"
    raise ValueError(
        f"Unsupported algebra for SDF embedding: {type(alg).__name__} "
        f"(dim={alg.dim}, sig={alg.sig})"
    )


def get_spec(alg) -> AlgebraSpec:
    """Return the embedding spec for an algebra."""
    return _SPECS[algebra_name(alg)]


def _result_ids(alg) -> list[int]:
    """Full-algebra result blade ids (ascending; scalar at slot 0)."""
    return sorted(range(alg.algebra_dim))


def _point_coeffs(alg, x: float, y: float, z: float) -> dict[int, float]:
    """OPNS point coefficients for *alg* (used by tests/validation only)."""
    name = algebra_name(alg)
    if name == "e3":
        return {1: x, 2: y, 4: z}
    if name == "p3":
        return {1: x, 2: y, 4: z, 8: 1.0}
    if name == "n3":
        r2 = x * x + y * y + z * z
        return {1: x, 2: y, 4: z, 8: 0.5 * (r2 - 1.0), 16: 0.5 * (r2 + 1.0)}
    return {
        7: 1.0,
        11: -z,
        13: y,
        14: -x,
        19: -z,
        21: y,
        22: -x,
    }


def _bound_wire(bound: Any | None, spec: AlgebraSpec) -> dict[str, Any] | None:
    """Normalize a ``bound`` value to the ``mv_sdf`` wire form.

    ``None`` → the algebra's default bound (or no bound); a 3-sequence → a clip
    box of half-extents; a dict → passed through unchanged.
    """
    if bound is None:
        if spec.default_bound is None:
            return None
        return {"halfExtents": list(spec.default_bound)}
    if isinstance(bound, dict):
        return bound
    if isinstance(bound, (tuple, list)):
        return {"halfExtents": [float(v) for v in bound]}
    raise TypeError(
        f"bound must be None, a 3-sequence, or a dict; got {bound!r}"
    )


def embed_entity_mv(
    mv: MV,
    *,
    normalize: bool = True,
    bound: Any | None = None,
    distance: str = "scalar_pseudo",
) -> dict[str, Any]:
    """Reduce *mv* to the ``mv_sdf`` wire core (no id/color/style fields).

    Returns a dict with ``algebra``, ``product``, ``distance``, ``normalize``,
    ``point_ids``, ``result_ids``, ``slot_pseudo``, ``M`` (flattened row-major
    over result × point), ``scale`` (1.0; calibrated in Phase 9), and ``bound``.
    """
    alg = mv.algebra
    spec = get_spec(alg)

    if normalize:
        mv = mv.normalized()

    product = EProduct.OP if mv.opns else EProduct.IP

    point_mask = BladeMask(alg, spec.point_ids)
    entity_mask = BladeMask(mv)
    result_mask = BladeMask(alg, _result_ids(alg))

    entity_coeffs = np.array([mv[bid] for bid in entity_mask.ids], dtype=float)
    entity_tensor = MVTensor(data=entity_coeffs, masks=(entity_mask,))

    # O encodes `point ∘ entity = result` (left=True → A∘B, A=point, B=entity).
    op_tensor = product_tensor(
        point_mask, entity_mask, result_mask, product=product, left=True
    )
    # Bake the entity in by contracting the entity operand axis (b).
    m_tensor = contract("cab,b->ca", op_tensor, entity_tensor)

    result_ids = list(result_mask.ids)
    point_ids = list(spec.point_ids)
    slot_pseudo = result_ids.index(alg.pseudoscalar_id)

    return {
        "algebra": spec.name,
        "product": "op" if product is EProduct.OP else "ip",
        "distance": distance,
        "normalize": bool(normalize),
        "point_ids": point_ids,
        "result_ids": result_ids,
        "slot_pseudo": slot_pseudo,
        "M": np.asarray(m_tensor.data, dtype=float).reshape(-1).tolist(),
        "scale": 1.0,
        "bound": _bound_wire(bound, spec),
    }


def embed_src(alg) -> str:
    """Return the full ``evalPoint<ALGEBRA>`` GLSL function for *alg*.

    The emitted function matches the ``point_ids`` order used by
    :func:`embed_entity_mv` (and mirrored in ``embeds.js``).
    """
    spec = get_spec(alg)
    name = spec.name.upper()
    np_ = len(spec.point_ids)
    return (
        f"void evalPoint{name}(vec3 p, out float a[{np_}]) {{"
        f"{spec.point_body}\n"
        "}"
    )
