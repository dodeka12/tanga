# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""CPU reference tests for the `DepthImage` grazing-angle (stretch) filter.

Mirrors the per-vertex slope that ``depth-shader.js`` computes, so the
angle→discard semantics (which triangles are flagged) are locked independently
of the GLSL.  ``compute_pinhole_positions`` is the canonical reference for the
frontend vertex math; the stretch is the max over the four neighbour pairs of
``|zN − zC| · f / (zC · Δref)`` (u uses ``fx``, v uses ``fy``).
"""

from __future__ import annotations

import math

import numpy as np

from pytanga.viz.depth_image import compute_pinhole_positions


def _vertex_stretch(
    depth: np.ndarray, fx: float, fy: float, cx: float, cy: float
) -> np.ndarray:
    """Return the per-vertex stretch (max apparent slope) for a pinhole depth map."""
    positions, u, v = compute_pinhole_positions(
        depth, fx=fx, fy=fy, cx=cx, cy=cy, depth_kind="axial"
    )
    h, w = depth.shape
    pos = positions.reshape(h, w, 3)
    uu = u.reshape(h, w)
    vv = v.reshape(h, w)
    z = pos[:, :, 2]

    # Reference-pixel spacing between adjacent mesh samples (≈1 at mesh_scale=1).
    du_ref = abs(float(uu[0, 1] - uu[0, 0]))
    dv_ref = abs(float(vv[1, 0] - vv[0, 0]))

    stretch = np.zeros((h, w), dtype=np.float64)
    for i in range(h):
        for j in range(w):
            zc = float(z[i, j])
            if zc <= 0.0:
                continue
            best = 0.0
            for jn in (j - 1, j + 1):
                if 0 <= jn < w:
                    best = max(best, abs(float(z[i, jn]) - zc) * fx / (zc * du_ref))
            for i_n in (i - 1, i + 1):
                if 0 <= i_n < h:
                    best = max(best, abs(float(z[i_n, j]) - zc) * fy / (zc * dv_ref))
            stretch[i, j] = best
    return stretch


def _box_plane_depth(n: int = 64) -> np.ndarray:
    """A central box at ``Z = 1.5`` in front of a plane at ``Z = 3.0``."""
    depth = np.full((n, n), 3.0, dtype=np.float32)
    lo, hi = n // 4, 3 * n // 4
    depth[lo:hi, lo:hi] = 1.5
    return depth


def _tilted_plane_depth(n: int = 64, fx: float = 400.0) -> np.ndarray:
    """A plane whose normal is 60° from the ray (surface 30° from the ray)."""
    cx = (n - 1) / 2.0
    u = np.arange(n, dtype=np.float64)
    xnorm = (u - cx) / fx
    phi = math.radians(60.0)
    d = 3.0 * math.cos(phi)
    z = d / (math.cos(phi) + math.sin(phi) * xnorm)
    return np.tile(z, (n, 1)).astype(np.float32)


def test_box_border_discarded_and_interiors_kept() -> None:
    depth = _box_plane_depth()
    stretch = _vertex_stretch(depth, 400.0, 400.0, 31.5, 31.5)
    threshold = math.tan(math.radians(80.0))

    n = depth.shape[0]
    lo = n // 4
    mid = n // 2

    # Interiors are nearly flat (kept).
    assert stretch[lo + 8, lo + 8] < threshold  # inside box
    assert stretch[4, 4] < threshold  # inside plane
    # Border vertices (box side and plane side) are steep (discarded).
    assert stretch[lo, mid] > threshold
    assert stretch[lo - 1, mid] > threshold


def test_tilted_plane_stays_complete() -> None:
    depth = _tilted_plane_depth()
    stretch = _vertex_stretch(depth, 400.0, 400.0, 31.5, 31.5)
    threshold = math.tan(math.radians(80.0))
    assert stretch.max() > 0.5  # actually tilted, not flat
    assert stretch.max() < threshold
