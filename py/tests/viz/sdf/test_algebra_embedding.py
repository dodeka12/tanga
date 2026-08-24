# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the algebra SDF embedding backend (Phase 7)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from pytanga.blade_mask import BladeMask
from pytanga.geometry import create_entity
from pytanga.geometry.entities import Direction, Line, Plane, Point
from pytanga.viz.sdf.algebra_embedding import (
    algebra_name,
    embed_entity_mv,
    embed_src,
    get_spec,
)

EMBEDS_JS = (
    Path(__file__).parents[3]
    / "pytanga"
    / "viz"
    / "templates"
    / "sdf"
    / "algebra"
    / "embeds.js"
)

ALGEBRAS = ["e3", "p3", "n3", "pga3"]


def _basis(name: str):
    if name == "e3":
        from pytanga.basis.e3 import BasisE3

        return BasisE3(opns=True)
    if name == "p3":
        from pytanga.basis.p3 import BasisP3

        return BasisP3(opns=True)
    if name == "n3":
        from pytanga.basis.n3 import BasisN3

        return BasisN3(opns=True)
    if name == "pga3":
        from pytanga.basis.pga3 import BasisPGA3

        return BasisPGA3(opns=True)
    raise ValueError(name)


def _plane_mv(basis):
    return create_entity(
        basis, Plane(point=Point(0.0, 0.0, 0.0), normal=Direction(0.0, 0.0, 1.0))
    )


def _m_matrix(wire: dict) -> np.ndarray:
    return np.array(wire["M"], dtype=float).reshape(
        len(wire["result_ids"]), len(wire["point_ids"])
    )


@pytest.mark.parametrize("name", ALGEBRAS)
def test_m_reconstruction(name: str) -> None:
    basis = _basis(name)
    entity_mv = _plane_mv(basis)
    point_mv = create_entity(basis, Point(1.0, 2.0, 3.0))

    wire = embed_entity_mv(entity_mv, normalize=False)
    m = _m_matrix(wire)
    point_coeffs = np.array(
        [point_mv[bid] for bid in wire["point_ids"]], dtype=float
    )

    expected = basis.op(point_mv, entity_mv)
    expected_coeffs = np.array(
        [expected[bid] for bid in wire["result_ids"]], dtype=float
    )

    assert np.allclose(m @ point_coeffs, expected_coeffs, atol=1e-9)


@pytest.mark.parametrize("name", ALGEBRAS)
def test_shape_and_ordering(name: str) -> None:
    basis = _basis(name)
    wire = embed_entity_mv(_plane_mv(basis), normalize=False)

    assert len(wire["M"]) == len(wire["result_ids"]) * len(wire["point_ids"])
    # scalar at slot 0, pseudoscalar at the reported (last) slot.
    assert wire["result_ids"][0] == 0
    assert wire["result_ids"][wire["slot_pseudo"]] == basis.pseudoscalar_id
    assert wire["slot_pseudo"] == len(wire["result_ids"]) - 1
    # the wire form carries the fields Phase 8 consumes.
    for key in (
        "algebra", "product", "distance", "normalize", "M", "scale",
        "thickness", "falloff", "max_distance",
    ):
        assert key in wire


def test_p3_trivector() -> None:
    basis = _basis("p3")
    line_mv = create_entity(
        basis, Line(origin=Point(0.0, 0.0, 0.0), direction=Direction(1.0, 0.0, 0.0))
    )
    point_mv = create_entity(basis, Point(0.0, 1.0, 2.0))

    wire = embed_entity_mv(line_mv, normalize=False)
    m = _m_matrix(wire)
    point_coeffs = np.array(
        [point_mv[bid] for bid in wire["point_ids"]], dtype=float
    )
    r = m @ point_coeffs

    # grade-1 op grade-2 = grade-3 trivector: scalar blade zero, |r| nonzero.
    assert abs(r[0]) < 1e-9
    assert np.linalg.norm(r) > 1e-6


def test_normalize_scales() -> None:
    basis = _basis("p3")
    entity_mv = _plane_mv(basis)

    m_norm = np.array(embed_entity_mv(entity_mv, normalize=True)["M"], dtype=float)
    m_raw = np.array(embed_entity_mv(entity_mv, normalize=False)["M"], dtype=float)

    mag = float(entity_mv.mag)
    assert mag > 0.0
    assert np.allclose(m_norm * mag, m_raw, atol=1e-9)


@pytest.mark.parametrize("name", ALGEBRAS)
def test_embed_src_consistency(name: str) -> None:
    basis = _basis(name)
    spec = get_spec(basis)
    src = embed_src(basis)

    # point_ids match the support of the OPNS point.
    point_mv = create_entity(basis, Point(1.0, 2.0, 3.0))
    assert BladeMask(point_mv).ids == list(spec.point_ids)

    # the emitted function declares `a[NP]` and the canonical name.
    assert f"out float a[{len(spec.point_ids)}]" in src
    assert f"evalPoint{name.upper()}" in src

    # embeds.js carries a matching key with the same NP and a per-algebra
    # gradient snippet (Phase 13); NR/SLOT_PSEUDO are now per-object wire data.
    js = EMBEDS_JS.read_text(encoding="utf-8")
    assert f"'{name}'" in js
    assert f"NP: {len(spec.point_ids)}" in js
    assert "gradient:" in js
    assert "NR:" not in js
    assert "SLOT_PSEUDO:" not in js


def test_thickness_wire() -> None:
    from pytanga.viz.sdf.serializer import serialize_mv

    basis = _basis("p3")
    line = create_entity(
        basis, Line(origin=Point(0.0, 0.0, 0.0), direction=Direction(1.0, 1.0, 1.0))
    )

    wire = embed_entity_mv(line, normalize=False, thickness=0.1)
    assert wire["thickness"] == 0.1

    # The `thickness` prop is forwarded through the serializer (the mv_sdf path).
    out = serialize_mv(line, "line", {"thickness": 0.25})
    assert out["thickness"] == 0.25
    # Default is zero (no cutoff).
    assert serialize_mv(line, "line2", {})["thickness"] == 0.0


def test_soft_opacity_wire() -> None:
    from pytanga.viz.sdf.serializer import serialize_mv

    basis = _basis("p3")
    line = create_entity(
        basis, Line(origin=Point(0.0, 0.0, 0.0), direction=Direction(1.0, 1.0, 1.0))
    )

    wire = embed_entity_mv(line, normalize=False, falloff=0.2, max_distance=1.0)
    assert wire["falloff"] == 0.2
    assert wire["max_distance"] == 1.0

    out = serialize_mv(line, "line", {"falloff": 0.2, "max_distance": 1.0})
    assert out["falloff"] == 0.2
    assert out["max_distance"] == 1.0
    # Defaults are zero (no soft edge / no hard cutoff).
    assert serialize_mv(line, "line2", {})["falloff"] == 0.0
    assert serialize_mv(line, "line2", {})["max_distance"] == 0.0


def test_active_result_mask() -> None:
    """The result mask is the active product mask plus scalar + pseudoscalar.

    For the four demo entities, ``result_ids`` equals the exact non-zero result
    blades of ``point ∘ entity`` (plus the scalar and pseudoscalar blades), and
    the active ``M`` is the full-algebra ``M`` with its all-zero rows dropped.
    """
    from pytanga.algebra import EProduct
    from pytanga.blade_mask.predict import product_blade_mask
    from pytanga.geometry.entities import Circle, Sphere
    from pytanga.tensor import MVTensor
    from pytanga.tensor.ops import contract
    from pytanga.tensor.product import product_tensor

    entities = [
        create_entity(
            _basis("pga3"),
            Plane(point=Point(0.0, 0.0, 0.0), normal=Direction(0.0, 0.0, 1.0)),
        ),
        create_entity(
            _basis("p3"),
            Line(origin=Point(0.0, 0.0, 0.0), direction=Direction(1.0, 1.0, 1.0)),
        ),
        create_entity(
            _basis("n3"), Sphere(center=Point(1.0, 0.0, 0.0), radius=2.0)
        ),
        create_entity(
            _basis("n3"),
            Circle(center=Point(1.0, 1.0, 1.0), radius=4.0, normal=Direction(1.0, 1.0, 1.0)),
        ),
    ]
    for mv in entities:
        alg = mv.algebra
        wire = embed_entity_mv(mv, normalize=False)
        spec = get_spec(alg)
        product = EProduct.OP if mv.opns else EProduct.IP
        point_mask = BladeMask(alg, spec.point_ids)
        entity_mask = BladeMask(mv)

        # result_ids == active product mask ∪ {scalar, pseudoscalar}.
        active_ids = product_blade_mask(point_mask, entity_mask, product=product).ids
        assert wire["result_ids"] == sorted(set(active_ids) | {0, alg.pseudoscalar_id})

        # active M == full M with its all-zero rows dropped.
        full_mask = BladeMask(alg, sorted(range(alg.algebra_dim)))
        entity_tensor = MVTensor(
            data=np.array([mv[bid] for bid in entity_mask.ids], dtype=float),
            masks=(entity_mask,),
        )
        op_tensor = product_tensor(
            point_mask, entity_mask, full_mask, product=product, left=True
        )
        full_m = np.asarray(
            contract("cab,b->ca", op_tensor, entity_tensor).data, dtype=float
        ).reshape(len(full_mask.ids), len(spec.point_ids))
        active_m = _m_matrix(wire)
        full_by_id = {bid: full_m[i] for i, bid in enumerate(full_mask.ids)}
        expected_m = np.array([full_by_id[bid] for bid in wire["result_ids"]], dtype=float)
        assert np.allclose(active_m, expected_m, atol=1e-9)

        nonzero_ids = {
            full_mask.ids[i]
            for i in range(len(full_mask.ids))
            if not np.allclose(full_m[i], 0.0, atol=1e-12)
        }
        assert set(wire["result_ids"]) == nonzero_ids | {0, alg.pseudoscalar_id}


