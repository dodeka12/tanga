# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""Vertex generators for glTF 2.0 primitives.

Each function returns a ``_Primitive`` with positions, normals, and
indices suitable for glTF mesh construction.
"""

from __future__ import annotations

import math

import numpy as np


class _Primitive:
    """Generated vertex data for one mesh primitive."""

    def __init__(
        self,
        positions: np.ndarray,
        normals: np.ndarray,
        indices: np.ndarray,
        mode: int = 4,  # glTF TRIANGLES
    ) -> None:
        self.positions = positions
        self.normals = normals
        self.indices = indices
        self.mode = mode


def sphere(radius: float, segments: int = 16) -> _Primitive:
    """UV sphere (stacked rings). Returns TRIANGLES primitive."""
    lat_segments = max(3, segments)
    lon_segments = max(3, segments * 2)

    verts: list[tuple[float, float, float]] = []
    norms: list[tuple[float, float, float]] = []
    idx: list[int] = []

    for y in range(lat_segments + 1):
        theta = y * math.pi / lat_segments
        sin_theta = math.sin(theta)
        cos_theta = math.cos(theta)
        for x in range(lon_segments + 1):
            phi = x * 2 * math.pi / lon_segments
            sin_phi = math.sin(phi)
            cos_phi = math.cos(phi)
            nx = cos_phi * sin_theta
            ny = cos_theta
            nz = sin_phi * sin_theta
            verts.append((nx * radius, ny * radius, nz * radius))
            norms.append((nx, ny, nz))

    for y in range(lat_segments):
        for x in range(lon_segments):
            a = y * (lon_segments + 1) + x
            b = a + lon_segments + 1
            idx.extend([a, b, a + 1])
            idx.extend([b, b + 1, a + 1])

    return _Primitive(
        positions=np.array(verts, dtype=np.float32),
        normals=np.array(norms, dtype=np.float32),
        indices=np.array(idx, dtype=np.uint16),
    )


def cylinder(radius: float, height: float, segments: int = 16) -> _Primitive:
    """Cylinder centered on Y axis, from -height/2 to +height/2."""
    segs = max(3, segments)
    half_h = height / 2
    verts: list[tuple[float, float, float]] = []
    norms: list[tuple[float, float, float]] = []
    idx: list[int] = []

    # Side vertices
    for i in range(segs + 1):
        angle = i * 2 * math.pi / segs
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        verts.append((cos_a * radius, half_h, sin_a * radius))
        norms.append((cos_a, 0, sin_a))
        verts.append((cos_a * radius, -half_h, sin_a * radius))
        norms.append((cos_a, 0, sin_a))

    for i in range(segs):
        a = i * 2
        b = a + 2
        idx.extend([a, a + 1, b])
        idx.extend([a + 1, b + 1, b])

    # Top cap
    top_center = len(verts)
    verts.append((0.0, half_h, 0.0))
    norms.append((0.0, 1.0, 0.0))
    for i in range(segs + 1):
        angle = i * 2 * math.pi / segs
        verts.append((math.cos(angle) * radius, half_h, math.sin(angle) * radius))
        norms.append((0.0, 1.0, 0.0))
    for i in range(segs):
        idx.extend([top_center, top_center + 1 + i, top_center + 2 + i])

    # Bottom cap
    bot_center = len(verts)
    verts.append((0.0, -half_h, 0.0))
    norms.append((0.0, -1.0, 0.0))
    for i in range(segs + 1):
        angle = i * 2 * math.pi / segs
        verts.append((math.cos(angle) * radius, -half_h, math.sin(angle) * radius))
        norms.append((0.0, -1.0, 0.0))
    for i in range(segs):
        idx.extend([bot_center, bot_center + 2 + i, bot_center + 1 + i])

    return _Primitive(
        positions=np.array(verts, dtype=np.float32),
        normals=np.array(norms, dtype=np.float32),
        indices=np.array(idx, dtype=np.uint32),
    )


def cone(radius: float, height: float, segments: int = 16) -> _Primitive:
    """Cone centered on Y axis, apex at +height/2, base at -height/2."""
    segs = max(3, segments)
    half_h = height / 2
    verts: list[tuple[float, float, float]] = []
    norms: list[tuple[float, float, float]] = []
    idx: list[int] = []

    verts.append((0.0, half_h, 0.0))
    norms.append((0.0, 1.0, 0.0))

    for i in range(segs + 1):
        angle = i * 2 * math.pi / segs
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        verts.append((cos_a * radius, -half_h, sin_a * radius))
        ny_side = radius / math.sqrt(radius * radius + height * height)
        norms.append(
            (
                cos_a * ny_side,
                height / math.sqrt(radius * radius + height * height),
                sin_a * ny_side,
            )
        )

    for i in range(segs):
        idx.extend([0, 1 + i + 1, 1 + i])

    bot_center = len(verts)
    verts.append((0.0, -half_h, 0.0))
    norms.append((0.0, -1.0, 0.0))
    for i in range(segs + 1):
        angle = i * 2 * math.pi / segs
        verts.append((math.cos(angle) * radius, -half_h, math.sin(angle) * radius))
        norms.append((0.0, -1.0, 0.0))
    for i in range(segs):
        idx.extend([bot_center, bot_center + 2 + i, bot_center + 1 + i])

    return _Primitive(
        positions=np.array(verts, dtype=np.float32),
        normals=np.array(norms, dtype=np.float32),
        indices=np.array(idx, dtype=np.uint32),
    )


def plane(width: float, height: float) -> _Primitive:
    """Quad in the XY plane, centered at origin, Z = 0."""
    hw = width / 2
    hh = height / 2
    verts = np.array(
        [[-hw, -hh, 0], [hw, -hh, 0], [hw, hh, 0], [-hw, hh, 0]],
        dtype=np.float32,
    )
    norms = np.array([[0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1]], dtype=np.float32)
    idx = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint16)
    return _Primitive(positions=verts, normals=norms, indices=idx)


def torus(
    major_radius: float,
    minor_radius: float,
    torus_segments: int = 32,
    tube_segments: int = 16,
) -> _Primitive:
    """Torus in the XY plane, centered at origin."""
    t_segs = max(3, torus_segments)
    tube_segs = max(3, tube_segments)
    verts: list[tuple[float, float, float]] = []
    norms: list[tuple[float, float, float]] = []
    idx: list[int] = []

    for i in range(t_segs + 1):
        theta = i * 2 * math.pi / t_segs
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        cx = cos_t * major_radius
        cy = sin_t * major_radius
        for j in range(tube_segs + 1):
            phi = j * 2 * math.pi / tube_segs
            cos_p = math.cos(phi)
            sin_p = math.sin(phi)
            verts.append(
                (
                    cx + cos_t * cos_p * minor_radius,
                    cy + sin_t * cos_p * minor_radius,
                    sin_p * minor_radius,
                )
            )
            norms.append((cos_t * cos_p, sin_t * cos_p, sin_p))

    for i in range(t_segs):
        for j in range(tube_segs):
            a = i * (tube_segs + 1) + j
            b = a + tube_segs + 1
            idx.extend([a, b, a + 1])
            idx.extend([b, b + 1, a + 1])

    return _Primitive(
        positions=np.array(verts, dtype=np.float32),
        normals=np.array(norms, dtype=np.float32),
        indices=np.array(idx, dtype=np.uint32),
    )


def box_edges(extent: float) -> _Primitive:
    """Wireframe box edges as a LINES primitive. ``extent`` is half-size."""
    e = extent
    corners = np.array(
        [
            [-e, -e, -e],
            [e, -e, -e],
            [e, e, -e],
            [-e, e, -e],
            [-e, -e, e],
            [e, -e, e],
            [e, e, e],
            [-e, e, e],
        ],
        dtype=np.float32,
    )
    edge_idx = [
        0,
        1,
        1,
        2,
        2,
        3,
        3,
        0,
        4,
        5,
        5,
        6,
        6,
        7,
        7,
        4,
        0,
        4,
        1,
        5,
        2,
        6,
        3,
        7,
    ]
    pos = np.array([corners[i] for i in edge_idx], dtype=np.float32)
    norms = np.zeros_like(pos)
    idx = np.arange(24, dtype=np.uint16)
    return _Primitive(positions=pos, normals=norms, indices=idx, mode=1)


def ring(
    inner_radius: float, outer_radius: float, angle: float, segments: int = 32
) -> _Primitive:
    """Partial ring (disc sector) in the XY plane."""
    segs = max(3, segments)
    verts: list[tuple[float, float, float]] = []
    norms: list[tuple[float, float, float]] = []
    idx: list[int] = []

    for i in range(segs + 1):
        a = angle * i / segs
        cos_a = math.cos(a)
        sin_a = math.sin(a)
        verts.append((cos_a * inner_radius, sin_a * inner_radius, 0))
        norms.append((0, 0, 1))
        verts.append((cos_a * outer_radius, sin_a * outer_radius, 0))
        norms.append((0, 0, 1))

    for i in range(segs):
        a = i * 2
        b = a + 2
        idx.extend([a, a + 1, b])
        idx.extend([a + 1, b + 1, b])

    return _Primitive(
        positions=np.array(verts, dtype=np.float32),
        normals=np.array(norms, dtype=np.float32),
        indices=np.array(idx, dtype=np.uint32),
    )


def lines_from_points(
    points: list[tuple[float, float, float]],
) -> _Primitive | None:
    """Build a ``LINES`` primitive from a list of 3D points.

    Each consecutive pair ``(points[i], points[i+1])`` forms a line segment.
    Returns ``None`` if fewer than 2 points are provided.
    """
    if len(points) < 2:
        return None

    n = len(points)
    pos = np.array(points, dtype=np.float32)
    norms = np.zeros_like(pos)

    # Build segment indices: [0,1, 1,2, 2,3, ...]
    seg_count = n - 1
    indices = np.zeros(seg_count * 2, dtype=np.uint16)
    for i in range(seg_count):
        indices[i * 2] = i
        indices[i * 2 + 1] = i + 1

    return _Primitive(positions=pos, normals=norms, indices=indices, mode=1)


def lines_from_segments(
    segments: list[tuple[tuple[float, float, float], tuple[float, float, float]]],
) -> _Primitive | None:
    """Build a ``LINES`` primitive from explicit start/end point pairs.

    Each segment is an independent line — unlike :func:`lines_from_points`,
    consecutive pairs are not implicitly connected.  Returns ``None`` if no
    segments are provided.
    """
    if not segments:
        return None

    pts: list[tuple[float, float, float]] = []
    for a, b in segments:
        pts.append(a)
        pts.append(b)

    pos = np.array(pts, dtype=np.float32)
    norms = np.zeros_like(pos)

    n = len(segments)
    indices = np.arange(n * 2, dtype=np.uint16)
    return _Primitive(positions=pos, normals=norms, indices=indices, mode=1)


def helix_tube(
    radius: float,
    tube_radius: float,
    height: float,
    total_angle: float,
    axis: tuple[float, float, float] = (0.0, 1.0, 0.0),
    path_segments: int = 64,
    tube_segments: int = 8,
) -> _Primitive:
    """Tube extruded along a helix path around *axis*.

    The helix moves from ``-height/2`` to ``+height/2`` along the axis
    while rotating ``total_angle`` radians around it.  At each step a
    ring of ``tube_segments`` vertices is swept perpendicular to the
    tangent, and consecutive rings are connected with triangle strips.

    The geometry is built axis-agnostically: an orthonormal frame
    ``(u, v)`` perpendicular to *axis* is chosen, and the centreline
    is ``p(t) = t·height·axis + radius·(cos θ(t)·u + sin θ(t)·v)``.

    Args:
        radius: Distance of the helix centreline from the axis.
        tube_radius: Tube cross-section radius.
        height: Total extent along the axis.
        total_angle: Total rotation angle (radians) over the height.
        axis: Direction vector of the helix axis (need not be unit).
        path_segments: Number of steps along the centreline.
        tube_segments: Number of vertices per ring cross-section.

    Returns:
        A ``_Primitive`` with mode TRIANGLES.
    """
    # Normalise axis
    ax, ay, az = axis
    a_len = math.sqrt(ax * ax + ay * ay + az * az)
    if a_len < 1e-10:
        ax, ay, az = 0.0, 1.0, 0.0  # fallback
    else:
        ax, ay, az = ax / a_len, ay / a_len, az / a_len

    # Build an orthonormal frame perpendicular to the axis
    if abs(ax) < 0.9:
        ux, uy, uz = -az, 0.0, ax
    else:
        ux, uy, uz = 0.0, az, -ay
    u_len = math.sqrt(ux * ux + uy * uy + uz * uz)
    ux, uy, uz = ux / u_len, uy / u_len, uz / u_len

    vx = ay * uz - az * uy
    vy = az * ux - ax * uz
    vz = ax * uy - ay * ux

    ps = max(3, path_segments)
    ts = max(3, tube_segments)
    half_h = height / 2

    verts: list[tuple[float, float, float]] = []
    norms: list[tuple[float, float, float]] = []
    indices: list[int] = []

    for i in range(ps + 1):
        t = i / ps
        angle = t * total_angle
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Centreline point
        cx = t * height * ax - half_h * ax + radius * (cos_a * ux + sin_a * vx)
        cy = t * height * ay - half_h * ay + radius * (cos_a * uy + sin_a * vy)
        cz = t * height * az - half_h * az + radius * (cos_a * uz + sin_a * vz)

        # Tangent direction at this point
        tx = height * ax + radius * total_angle * (-sin_a * ux + cos_a * vx)
        ty = height * ay + radius * total_angle * (-sin_a * uy + cos_a * vy)
        tz = height * az + radius * total_angle * (-sin_a * uz + cos_a * vz)
        t_len = math.sqrt(tx * tx + ty * ty + tz * tz)
        tx, ty, tz = tx / t_len, ty / t_len, tz / t_len

        # Local ring frame: two perpendiculars to the tangent
        if abs(tx) < 0.9:
            ru_x, ru_y, ru_z = 0.0, -tz, ty
        else:
            ru_x, ru_y, ru_z = -tz, 0.0, tx
        ru_len = math.sqrt(ru_x * ru_x + ru_y * ru_y + ru_z * ru_z)
        ru_x, ru_y, ru_z = ru_x / ru_len, ru_y / ru_len, ru_z / ru_len

        rv_x = ty * ru_z - tz * ru_y
        rv_y = tz * ru_x - tx * ru_z
        rv_z = tx * ru_y - ty * ru_x

        for j in range(ts + 1):
            phi = j * 2 * math.pi / ts
            cos_p = math.cos(phi)
            sin_p = math.sin(phi)
            nx = ru_x * cos_p + rv_x * sin_p
            ny = ru_y * cos_p + rv_y * sin_p
            nz = ru_z * cos_p + rv_z * sin_p
            verts.append(
                (cx + nx * tube_radius, cy + ny * tube_radius, cz + nz * tube_radius)
            )
            norms.append((nx, ny, nz))

    # Triangle strips connecting consecutive rings
    ring_size = ts + 1
    for i in range(ps):
        base = i * ring_size
        next_base = base + ring_size
        for j in range(ts):
            a = base + j
            b = next_base + j
            indices.extend([a, b, a + 1])
            indices.extend([b, b + 1, a + 1])

    return _Primitive(
        positions=np.array(verts, dtype=np.float32),
        normals=np.array(norms, dtype=np.float32),
        indices=np.array(indices, dtype=np.uint32),
    )
