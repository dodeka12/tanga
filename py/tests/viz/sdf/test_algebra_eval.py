# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Headless smoke checks for the algebra SDF evaluator (Phase 8).

The real GLSL compile check needs a WebGL2 context (exercised in the browser,
and in the dev Node smoke ``dev/src/sdf_algebra_smoke.mjs``). These tests catch
the registry/assembly wiring errors early: the ``embeds.js``/``distances.js``/
``eval.js`` contract, the export surface, and the absence of GLSL identity
branching in the emitters.
"""

from __future__ import annotations

from pathlib import Path

from pytanga.viz.sdf.distance import DistanceFunction

SDC_DIR = Path(__file__).parents[3] / "pytanga" / "viz" / "templates" / "sdf"
ALG_DIR = SDC_DIR / "algebra"


def _read(name: str) -> str:
    return (ALG_DIR / name).read_text(encoding="utf-8")


def test_embeds_registry_complete() -> None:
    js = _read("embeds.js")
    assert "embedFuncs" in js
    for name in ("e3", "p3", "n3", "pga3"):
        assert f"'{name}'" in js, f"{name} missing from embeds.js"
    for token in ("NP:", "snippet:", "gradient:"):
        assert token in js, f"{token} missing from an embeds.js entry"
    assert "NR:" not in js, "NR: should be gone (now per-object wire data)"
    assert "SLOT_PSEUDO:" not in js, "SLOT_PSEUDO: should be gone (now per-object wire data)"


def test_eval_exports() -> None:
    js = _read("eval.js")
    for symbol in (
        "MAX_MV_FLOATS",
        "distFnName",
        "mvLayout",
        "distinctEmbedSrcs",
        "matrixUniformDecls",
        "emitDistanceFunctions",
        "emitAlgebraLeaves",
        "buildAlgebraUniforms",
    ):
        assert f"export const {symbol}" in js or f"export function {symbol}" in js, (
            f"{symbol} missing from eval.js"
        )


def test_distance_registry_names_present() -> None:
    js = _read("distances.js")
    for member in DistanceFunction:
        assert member.glsl_name in js, f"{member.glsl_name} missing from distances.js"


def test_no_shader_identity_branching_in_eval() -> None:
    # The emitters must never emit GLSL `if (algebra/distance/entity/opacity ==
    # …)` identity branching — the selection is resolved entirely at compile
    # time (JS-side string concatenation), never in the shader.
    js = _read("eval.js")
    for pattern in (
        "if (algebra ==",
        "if (distance ==",
        "if (entity ==",
        "if (opacity ==",
    ):
        assert pattern not in js, f"shader identity-branch pattern {pattern!r} in eval.js"


def test_distance_registry_derivative_documented() -> None:
    # Each distance function documents its closed-form derivative (Phase 13).
    js = _read("distances.js")
    assert js.count("derivative:") == len(list(DistanceFunction))


def test_branchless_gradient_guard() -> None:
    # The per-mask gradient uses a branchless 1/sqrt guard, never `if (rest < eps)`,
    # and distance functions are deduped per distinct result mask.
    js = _read("eval.js")
    assert "inversesqrt(rest + float(rest < 1e-6) * 1e-6)" in js
    assert "if (rest <" not in js
    assert "ids.join(',')" in js
    assert "maskSuffix" in js


def test_scene_builder_delegates_mv_sdf() -> None:
    sb = (SDC_DIR / "scene-builder.js").read_text(encoding="utf-8")
    assert "sdfKind === 'mv_sdf'" in sb
    assert "dist_mv_" in sb


def test_composer_passes_index() -> None:
    composer = (SDC_DIR / "composer.js").read_text(encoding="utf-8")
    assert "buildObjectExpr(obj, index)" in composer


def test_algebra_sdf_zero_set_matches_plane() -> None:
    """Numeric spot-check: the algebra SDF of a plane vanishes on the plane.

    ``scalar_pseudo(point op plane)`` is proportional to the point-to-plane
    distance (the residual scale is the Phase 9 calibration target). This is the
    headless stand-in for the browser "renders identically" check.
    """
    import numpy as np

    from pytanga.basis.pga3 import BasisPGA3
    from pytanga.geometry import create_entity
    from pytanga.geometry.entities import Direction, Plane, Point
    from pytanga.viz.sdf.algebra_embedding import embed_entity_mv

    basis = BasisPGA3(opns=True)
    plane = create_entity(
        basis, Plane(point=Point(0.0, 0.0, 0.0), normal=Direction(0.0, 0.0, 1.0))
    )
    wire = embed_entity_mv(plane, normalize=False)
    m = np.array(wire["M"]).reshape(len(wire["result_ids"]), len(wire["point_ids"]))

    def sdf(x: float, y: float, z: float) -> float:
        pt = create_entity(basis, Point(x, y, z))
        a = np.array([pt[bid] for bid in wire["point_ids"]], dtype=float)
        r = m @ a
        rest = sum(
            r[i] * r[i]
            for i in range(len(r))
            if i != 0 and i != wire["slot_pseudo"]
        )
        return float(r[0] + r[wire["slot_pseudo"]] + np.sqrt(rest))

    assert abs(sdf(1.0, 2.0, 0.0)) < 1e-9  # on the plane → zero
    d1 = sdf(1.0, 2.0, 1.0)
    d2 = sdf(1.0, 2.0, 2.0)
    assert d1 > 0.0 and d2 > 0.0  # off-plane → positive
    assert abs(d2 - 2.0 * d1) < 1e-9  # proportional to the metric distance

