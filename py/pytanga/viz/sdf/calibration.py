# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase 9: gradient calibration + algebra-vs-analytic validation helpers.

The algebra SDF ``d = distOf(M·a)`` is proportional to — but not exactly — the
Euclidean distance. ``normalize=True`` removes the entity's own magnitude, but a
residual per-algebra/entity scale can remain, making sphere-tracing step too far
(miss) or too short (banding). These helpers estimate that scale with a
finite-difference gradient probe and expose it for the per-object ``scale``
uniform (already wired through Phases 7/8).

Calibration table (plane through origin, normal +z, ``scalar_pseudo``):

- ``e3``   → ``d = -z``   (signed, scale 1)
- ``p3``   → ``d = +z``   (signed, scale 1)
- ``n3``   → ``d = -z``   (signed, scale 1)
- ``pga3`` → ``d = |z|·√2`` (unsigned, scale 1/√2)

The per-algebra sign of the signed modes comes from the scalar + pseudoscalar
blades of the result (``r[0] + r[I]``); ``pga3``'s point∧plane meet is a
grade-(dim−1) blade, so its ``scalar_pseudo`` is the magnitude only (unsigned).
``magnitude`` is always unsigned (zero-set only). Auto sign-flipping for
interior/exterior shading is deferred: it only matters for closed entities in
signed modes and is entity-orientation dependent, not a global per-algebra flip.
"""

from __future__ import annotations

import numpy as np

from pytanga.algebra import MV

from .algebra_embedding import embed_entity_mv, point_coeffs


def distance_value(
    r,
    slot_pseudo: int,
    distance: str = "scalar_pseudo",
    result_ids: list[int] | None = None,
) -> float:
    """Apply a distance function to a result coefficient vector ``r``.

    Mirrors the fixed ``distOf`` set (``distances.js``); ``grade``/``component``
    use the same defaults the Phase 8 shader uses (``k=1``, ``blade_id=0``).

    ``result_ids`` maps each ``r`` slot to its blade id (the active result mask).
    When omitted, the full-layout ``0..len(r)-1`` is assumed (backward
    compatible); ``grade`` uses it to resolve the *blade* grade of each slot.
    """
    if result_ids is None:
        result_ids = list(range(len(r)))
    if distance == "scalar_pseudo":
        rest = sum(
            float(v) ** 2 for i, v in enumerate(r) if i != 0 and i != slot_pseudo
        )
        return float(r[0]) + float(r[slot_pseudo]) + float(np.sqrt(rest))
    if distance == "magnitude":
        return float(np.linalg.norm(r))
    if distance == "scalar":
        return float(r[0])
    if distance == "grade":
        return float(
            np.linalg.norm(
                [v for i, v in enumerate(r) if bin(result_ids[i]).count("1") == 1]
            )
        )
    if distance == "component":
        return float(r[0])
    raise ValueError(f"Unknown distance function: {distance!r}")


def evaluate_sdf(
    mv: MV,
    x: float,
    y: float,
    z: float,
    *,
    normalize: bool = True,
    distance: str = "scalar_pseudo",
) -> float:
    """Evaluate the algebra SDF ``d(p)`` for *mv* at the point ``(x, y, z)``."""
    wire = embed_entity_mv(mv, normalize=normalize, distance=distance)
    m = np.array(wire["M"], dtype=float).reshape(
        len(wire["result_ids"]), len(wire["point_ids"])
    )
    pc = point_coeffs(mv.algebra, x, y, z)
    a = np.array([pc[bid] for bid in wire["point_ids"]], dtype=float)
    r = m @ a
    return distance_value(
        r, wire["slot_pseudo"], distance, result_ids=wire["result_ids"]
    )


def gradient(
    mv: MV,
    x: float,
    y: float,
    z: float,
    *,
    normalize: bool = True,
    distance: str = "scalar_pseudo",
    step: float = 1e-3,
) -> np.ndarray:
    """Central finite-difference gradient ``∇d`` at ``(x, y, z)``."""

    def f(px: float, py: float, pz: float) -> float:
        return evaluate_sdf(mv, px, py, pz, normalize=normalize, distance=distance)

    gx = (f(x + step, y, z) - f(x - step, y, z)) / (2.0 * step)
    gy = (f(x, y + step, z) - f(x, y - step, z)) / (2.0 * step)
    gz = (f(x, y, z + step) - f(x, y, z - step)) / (2.0 * step)
    return np.array([gx, gy, gz], dtype=float)


def gradient_norm(
    mv: MV,
    x: float,
    y: float,
    z: float,
    *,
    normalize: bool = True,
    distance: str = "scalar_pseudo",
    step: float = 1e-3,
) -> float:
    """``|∇d|`` at ``(x, y, z)``."""
    g = gradient(mv, x, y, z, normalize=normalize, distance=distance, step=step)
    return float(np.linalg.norm(g))


def scale_at(
    mv: MV,
    x: float,
    y: float,
    z: float,
    *,
    normalize: bool = True,
    distance: str = "scalar_pseudo",
    step: float = 1e-3,
) -> float:
    """Per-object scale ``s = 1/|∇d|`` near the surface point ``(x, y, z)``.

    Evaluates the gradient offset from the surface point, so the (possibly
    unsigned) distance field's ``|·|`` cusp at ``d = 0`` does not zero the
    central difference. A single offset direction can be parallel to the entity
    (e.g. ``(step, step, step)`` along a line through the origin in that
    direction), so several offset directions are probed and the largest gradient
    norm is taken.
    """
    gn = 0.0
    # Offset well beyond the central-difference step so the samples stay off the
    # `|·|` cusp (and off the entity), but close enough that `|∇d|` is still the
    # surface value. `offset` is the distance the probe point sits from the
    # surface; `step` is the finite-difference spacing around it.
    offset = 10.0 * step
    for dx, dy, dz in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 1.0, 1.0)):
        g = gradient(
            mv,
            x + offset * dx,
            y + offset * dy,
            z + offset * dz,
            normalize=normalize,
            distance=distance,
            step=step,
        )
        gn = max(gn, float(np.linalg.norm(g)))
    if gn < 1e-9:
        return 1.0
    return 1.0 / gn


_PROBE_STEPS = (
    (1.0, 0.0, 0.0),
    (-1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, -1.0, 0.0),
    (0.0, 0.0, 1.0),
    (0.0, 0.0, -1.0),
    (1.0, 1.0, 1.0),
    (-1.0, -1.0, -1.0),
)


def find_surface_point(
    mv: MV,
    *,
    normalize: bool = True,
    distance: str = "scalar_pseudo",
    start: tuple[float, float, float] = (0.0, 0.0, 0.0),
    iters: int = 200,
    tol: float = 1e-6,
) -> tuple[float, float, float]:
    """Gradient-descent to a surface point (``d ≈ 0``) starting at *start*.

    The algebra "distance" of a closed entity (a circle, a sphere) is *not*
    monotonic: it has a stationary point at the centre (gradient ≈ 0 with d > 0).
    When the descent lands on such a point it nudges outward — toward whichever
    probe direction most reduces ``|d|`` — and continues, so it still reaches the
    surface instead of getting stuck.
    """
    p = np.array(start, dtype=float)
    for _ in range(iters):
        d = evaluate_sdf(mv, *p, normalize=normalize, distance=distance)
        if abs(d) < tol:
            break
        g = gradient(mv, *p, normalize=normalize, distance=distance)
        gn = float(np.linalg.norm(g))
        if gn < 1e-9:
            step = max(abs(d), 0.1)
            best = None
            best_abs = abs(d)
            for dx, dy, dz in _PROBE_STEPS:
                q = p + np.array((dx, dy, dz), dtype=float) * step
                qd = abs(evaluate_sdf(mv, *q, normalize=normalize, distance=distance))
                if qd < best_abs:
                    best_abs = qd
                    best = q
            if best is None:
                break
            p = best
            continue
        p = p - (d / gn) * g
    return (float(p[0]), float(p[1]), float(p[2]))


def calibrate_scale(
    mv: MV,
    *,
    normalize: bool = True,
    distance: str = "scalar_pseudo",
    start: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> float:
    """Compute the per-object scale so ``|∇d| ≈ 1`` near the surface.

    Finds a surface point (gradient descent from *start*) and returns ``1/|∇d|``
    there.
    """
    sp = find_surface_point(mv, normalize=normalize, distance=distance, start=start)
    return scale_at(mv, *sp, normalize=normalize, distance=distance)
