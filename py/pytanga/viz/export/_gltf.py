# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""glTF 2.0 binary (``.glb``) builder for Tanga 3D viewer.

Translates serialized entity dicts into glTF 2.0 meshes, materials,
nodes, and a camera — then packs everything into a .glb binary file.

See the glTF 2.0 spec: https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
"""

from __future__ import annotations

import json
import math
import struct
from typing import Any, Dict, List, Tuple

import numpy as np

from . import _gltf_primitives as _prims
from ._gltf_primitives import _Primitive

# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════
_GLTF_MAGIC = 0x46546C67
_GLTF_VERSION = 2
_JSON_CHUNK_TYPE = 0x4E4F534A
_BIN_CHUNK_TYPE = 0x004E4942


def build_gltf_scene(
    entities: List[Dict[str, Any]],
    config: Any,
    labels: List[Dict[str, Any]] | None = None,
) -> bytes:
    """Build a glTF 2.0 binary (``.glb``) file from entity data.

    Args:
        entities: Serialized entity dicts from ``Scene.full_state()``.
        config: ``SceneConfig`` instance.
        labels: Serialized label dicts (ignored — glTF has no text primitive).
    """
    builder = _GltfBuilder()
    builder.add_entities(entities)
    if config.camera is not None:
        builder.add_camera(config.camera)
    return builder.finalize()


# ═══════════════════════════════════════════════════════════════
# Builder
# ═══════════════════════════════════════════════════════════════


class _GltfBuilder:
    """Assembles a glTF 2.0 scene from entity data."""

    def __init__(self) -> None:
        self._nodes: List[dict] = []
        self._meshes: List[dict] = []
        self._materials: List[dict] = []
        self._scene_nodes: List[int] = []
        self._buf_parts: List[bytes] = []
        self._buf_offset = 0
        self._accessors: List[dict] = []
        self._buffer_views: List[dict] = []
        self._cameras: List[dict] = []
        self._camera_node: int | None = None

    # ── Material helpers ────────────────────────────────

    def _get_or_create_material(self, color_hex: str, opacity: float) -> int:
        c = _hex_to_rgba(color_hex)
        c[3] = opacity
        key = (color_hex, opacity)
        for i, m in enumerate(self._materials):
            if (m.get("_tc", ""), m.get("_to", 1.0)) == key:
                return i
        idx = len(self._materials)
        self._materials.append(
            {
                "pbrMetallicRoughness": {
                    "baseColorFactor": c,
                    "metallicFactor": 0.1,
                    "roughnessFactor": 0.5,
                },
                "alphaMode": "BLEND" if opacity < 1.0 else "OPAQUE",
                "doubleSided": False,
                "_tc": color_hex,
                "_to": opacity,
            }
        )
        return idx

    # ── Buffer writing ──────────────────────────────────

    def _write_buffer(self, data: np.ndarray) -> Tuple[int, int]:
        raw = data.tobytes()
        offset = self._buf_offset
        length = len(raw)
        pad_len = (4 - length % 4) % 4
        self._buf_parts.append(raw + b"\x00" * pad_len)
        self._buf_offset += length + pad_len
        return offset, length

    def _add_view(self, offset: int, length: int, target: int | None = None) -> int:
        idx = len(self._buffer_views)
        view: dict = {"buffer": 0, "byteOffset": offset, "byteLength": length}
        if target is not None:
            view["target"] = target
        self._buffer_views.append(view)
        return idx

    def _add_accessor(
        self, view: int, offset: int, count: int, comp_type: int, acc_type: str
    ) -> int:
        idx = len(self._accessors)
        self._accessors.append(
            {
                "bufferView": view,
                "byteOffset": offset,
                "count": count,
                "componentType": comp_type,
                "type": acc_type,
            }
        )
        return idx

    # ── Style helper ────────────────────────────────────

    @staticmethod
    def _style_val(ent: dict, key: str, fallback: float) -> float:
        style = ent.get("style", {})
        if isinstance(style, dict) and key in style:
            return float(style[key])
        if key in ent:
            return float(ent[key])
        return float(fallback)

    # ── Entity → primitives ─────────────────────────────

    def add_entities(self, entities: List[Dict[str, Any]]) -> None:
        for ent in entities:
            self._add_entity(ent)

    def _add_entity(self, ent: Dict[str, Any]) -> None:
        # kind = ent.get("kind", "")
        color = str(ent.get("color", "#ffffff"))
        opacity = float(ent.get("opacity", 1.0))
        mat_idx = self._get_or_create_material(color, opacity)
        prims = self._make_primitives(ent)
        if not prims:
            return

        mesh_idx = len(self._meshes)
        gltf_prims = [self._prim_to_gltf(p, mat_idx) for p in prims]
        self._meshes.append({"primitives": gltf_prims})

        node: dict = {"mesh": mesh_idx}
        pos = self._get_position(ent)
        if pos and any(p != 0 for p in pos):
            node["translation"] = list(pos)
        rot = self._get_rotation(ent)
        if rot and not (rot[0] == 0 and rot[1] == 0 and rot[2] == 0 and rot[3] == 1):
            node["rotation"] = list(rot)
        node_idx = len(self._nodes)
        self._nodes.append(node)
        self._scene_nodes.append(node_idx)

    def _make_primitives(self, ent: Dict[str, Any]) -> List[_Primitive]:
        kind = ent.get("kind", "")
        if kind in ("Point", "HPoint"):
            return [_prims.sphere(self._style_val(ent, "size", 0.08), 8)]
        elif kind == "Direction":
            length = self._style_val(ent, "length", 2.0)
            cyl = _prims.cylinder(0.04, length * 0.75, 8)
            cone = _prims.cone(0.10, length * 0.25, 8)
            cyl.positions[:, 1] += length * 0.75 / 2
            cone.positions[:, 1] += length * 0.75 + length * 0.25 / 2
            return [cyl, cone]
        elif kind == "Line":
            return [
                _prims.cylinder(
                    self._style_val(ent, "thickness", 0.03),
                    self._style_val(ent, "length", 20.0),
                    8,
                )
            ]
        elif kind in ("Plane", "ReflectionPlane"):
            e = self._style_val(ent, "extent", 10.0)
            return [_prims.plane(e * 2, e * 2)]
        elif kind == "Circle":
            return [
                _prims.torus(
                    max(float(ent.get("radius", 1)), 0.001),
                    max(self._style_val(ent, "tube_radius", 0.03), 0.001),
                    32,
                    12,
                )
            ]
        elif kind == "Sphere":
            return [_prims.sphere(max(float(ent.get("radius", 1)), 0.001), 16)]
        elif kind == "Space":
            return [_prims.box_edges(self._style_val(ent, "extent", 10.0))]
        elif kind == "PointPair":
            s = self._style_val(ent, "point_size", 0.06)
            pa = ent.get("pointA", [0, 0, 0])
            pb = ent.get("pointB", [0, 0, 0])
            s1, s2 = _prims.sphere(s, 8), _prims.sphere(s, 8)
            s1.positions += np.array(pa, dtype=np.float32)
            s2.positions += np.array(pb, dtype=np.float32)
            return [s1, s2]
        elif kind == "Inversion":
            return [_prims.sphere(max(float(ent.get("radius", 2.0)), 0.001), 16)]
        elif kind == "Rotor":
            dr = self._style_val(ent, "disc_radius", 1.5)
            ang = abs(float(ent.get("angle", 0)))
            if ang >= 2 * math.pi - 0.001:
                return [_prims.torus(dr, 0.03, 32, 8)]
            if ang > 0:
                return [_prims.ring(dr * 0.15, dr, ang, 32)]
            return [_prims.torus(dr, 0.03, 32, 8)]
        elif kind == "Translator":
            length = self._style_val(ent, "length", 3.0)
            cyl = _prims.cylinder(0.06, length * 0.75, 8)
            cone = _prims.cone(0.15, length * 0.25, 8)
            cyl.positions[:, 1] += length * 0.75 / 2
            cone.positions[:, 1] += length * 0.75 + length * 0.25 / 2
            return [cyl, cone]
        elif kind == "Dilator":
            n = int(self._style_val(ent, "ring_count", 4))
            mx = self._style_val(ent, "max_radius", 3.0)
            prims = []
            for i in range(n):
                t = n > 1 and i / (n - 1) or 0.5
                prims.append(_prims.torus(0.3 + t * (mx - 0.3), 0.02, 8, 8))
            return prims
        elif kind == "Motor":
            rotor = ent.get("rotor", {})
            axis = tuple(rotor.get("axis", [0.0, 1.0, 0.0]))  # type: ignore[arg-type]
            angle = float(rotor.get("angle", 1.5))
            translator = ent.get("translator", {})
            trans_vec = translator.get("vector", [0, 0, 0])
            trans_mag = math.sqrt(sum(v**2 for v in trans_vec))
            # Helix tube around the rotation axis
            return [
                _prims.helix_tube(
                    1.0,
                    0.04,
                    trans_mag * 2,
                    angle,
                    axis=axis,
                    path_segments=24,
                    tube_segments=8,
                )
            ]
        elif kind == "GeneralRotor":
            return [_prims.torus(1.5, 0.02, 8, 8)]
        elif kind == "ReflectionLine":
            return [
                _prims.cylinder(
                    self._style_val(ent, "thickness", 0.04),
                    self._style_val(ent, "length", 5.0),
                    8,
                )
            ]
        return []

    @staticmethod
    def _get_position(ent: Dict[str, Any]) -> tuple[float, float, float] | None:
        kind = ent.get("kind", "")
        if kind in ("Point", "HPoint"):
            return tuple(ent.get("position", [0, 0, 0]))  # type: ignore[return-value]
        if kind in ("Direction", "Translator"):
            return tuple(ent.get("origin", [0, 0, 0]))  # type: ignore[return-value]
        if kind in ("Line",):
            return tuple(ent.get("origin", [0, 0, 0]))  # type: ignore[return-value]
        if kind in ("Plane", "ReflectionPlane"):
            return tuple(ent.get("point", ent.get("origin", [0, 0, 0])))  # type: ignore[return-value]
        if kind in ("Circle", "Sphere", "Inversion"):
            return tuple(ent.get("center", [0, 0, 0]))  # type: ignore[return-value]
        if kind in (
            "Rotor",
            "Motor",
            "GeneralRotor",
            "Dilator",
        ):
            return tuple(ent.get("origin", [0, 0, 0]))  # type: ignore[return-value]
        return (0.0, 0.0, 0.0)

    @staticmethod
    def _get_rotation(ent: Dict[str, Any]) -> tuple[float, float, float, float] | None:
        kind = ent.get("kind", "")
        normal: list[float] | None = None
        if kind in ("Plane", "ReflectionPlane", "Circle"):
            normal = ent.get("normal")
        elif kind in ("Rotor", "GeneralRotor"):
            normal = ent.get("axis")
        elif kind == "Motor":
            rotor = ent.get("rotor", {})
            normal = rotor.get("axis")
        elif kind == "ReflectionLine":
            normal = ent.get("direction")
        if normal and any(n != 0 for n in normal):
            n = np.array(normal, dtype=np.float64)
            n_len = np.linalg.norm(n)
            if n_len > 1e-10:
                n = n / n_len
                z = np.array([0.0, 0.0, 1.0])
                v = np.cross(z, n)
                w = 1.0 + np.dot(z, n)
                q_len = math.sqrt(w * w + v.dot(v))
                if q_len > 1e-10:
                    return (v[0] / q_len, v[1] / q_len, v[2] / q_len, w / q_len)
        return None

    def _prim_to_gltf(self, prim: _Primitive, mat_idx: int) -> dict:
        po, pl = self._write_buffer(prim.positions)
        no, nl = self._write_buffer(prim.normals)
        io, il = self._write_buffer(prim.indices)

        idx_ct = 5123 if prim.indices.dtype == np.uint16 else 5125
        pbv = self._add_view(po, pl, 34962)
        nbv = self._add_view(no, nl, 34962)
        ibv = self._add_view(io, il, 34963)
        return {
            "attributes": {
                "POSITION": self._add_accessor(
                    pbv, 0, len(prim.positions), 5126, "VEC3"
                ),
                "NORMAL": self._add_accessor(nbv, 0, len(prim.normals), 5126, "VEC3"),
            },
            "indices": self._add_accessor(ibv, 0, len(prim.indices), idx_ct, "SCALAR"),
            "material": mat_idx,
            "mode": prim.mode,
        }

    # ── Camera ──────────────────────────────────────────

    def add_camera(self, cam_config: Any) -> None:
        cam_idx = len(self._cameras)
        self._cameras.append(
            {
                "type": "perspective",
                "perspective": {
                    "aspectRatio": 16.0 / 9.0,
                    "yfov": (cam_config.fov or 50.0) * math.pi / 180.0,
                    "znear": cam_config.near or 0.1,
                    "zfar": cam_config.far or 1000.0,
                },
            }
        )
        node: dict = {"camera": cam_idx}
        if cam_config.position:
            node["translation"] = list(cam_config.position)
        if cam_config.target:
            pos = cam_config.position or (0, 0, 10)
            tgt = cam_config.target
            fwd = np.array(
                [tgt[0] - pos[0], tgt[1] - pos[1], tgt[2] - pos[2]], dtype=np.float64
            )
            fwd_len = np.linalg.norm(fwd)
            if fwd_len > 1e-10:
                fwd /= fwd_len
                up = np.array([0.0, 1.0, 0.0])
                right = np.cross(up, fwd)
                rc = np.linalg.norm(right)
                if rc < 1e-6:
                    up = np.array([0.0, 0.0, 1.0])
                    right = np.cross(up, fwd)
                    rc = np.linalg.norm(right)
                right /= rc
                up = np.cross(fwd, right)
                rot_mat = np.column_stack([right, up, -fwd])
                node["rotation"] = list(_mat3_to_quat(rot_mat))
        node_idx = len(self._nodes)
        self._nodes.append(node)
        self._camera_node = node_idx

    # ── Finalize ────────────────────────────────────────

    def finalize(self) -> bytes:
        gltf: dict = {"asset": {"version": "2.0", "generator": "Tanga viz _gltf.py"}}
        if self._scene_nodes:
            sn = list(self._scene_nodes)
            if self._camera_node is not None:
                sn.append(self._camera_node)
            gltf.update(scene=0, scenes=[{"nodes": sn}])
        if self._nodes:
            gltf["nodes"] = self._nodes
        if self._meshes:
            gltf["meshes"] = self._meshes
        if self._accessors:
            gltf["accessors"] = self._accessors
        if self._buffer_views:
            gltf["bufferViews"] = self._buffer_views
        if self._materials:
            gltf["materials"] = [
                {k: v for k, v in m.items() if not k.startswith("_t")}
                for m in self._materials
            ]
        if self._cameras:
            gltf["cameras"] = self._cameras

        bin_data = b"".join(self._buf_parts)
        gltf["buffers"] = [{"byteLength": self._buf_offset}]

        json_bytes = json.dumps(gltf, separators=(",", ":")).encode()
        json_pad = (4 - len(json_bytes) % 4) % 4
        json_bytes += b" " * json_pad

        total = 12 + 8 + len(json_bytes) + 8 + len(bin_data)
        header = struct.pack("<III", _GLTF_MAGIC, _GLTF_VERSION, total)
        json_chunk = struct.pack("<II", len(json_bytes), _JSON_CHUNK_TYPE) + json_bytes
        bin_chunk = (
            struct.pack("<II", len(bin_data), _BIN_CHUNK_TYPE) + bin_data
            if bin_data
            else b""
        )
        return header + json_chunk + bin_chunk


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════


def _hex_to_rgba(hex_color: str) -> List[float]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) < 6:
        h = h.ljust(6, "0")
    r, g, b = int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0
    return [_srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b), 1.0]


def _srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _mat3_to_quat(m: np.ndarray) -> tuple[float, float, float, float]:
    trace = m[0, 0] + m[1, 1] + m[2, 2]
    if trace > 0:
        s = math.sqrt(trace + 1.0) * 2
        return (
            float((m[2, 1] - m[1, 2]) / s),
            float((m[0, 2] - m[2, 0]) / s),
            float((m[1, 0] - m[0, 1]) / s),
            float(0.25 * s),
        )
    if m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        return (
            float(0.25 * s),
            float((m[0, 1] + m[1, 0]) / s),
            float((m[0, 2] + m[2, 0]) / s),
            float((m[2, 1] - m[1, 2]) / s),
        )
    if m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        return (
            float((m[0, 1] + m[1, 0]) / s),
            float(0.25 * s),
            float((m[1, 2] + m[2, 1]) / s),
            float((m[0, 2] - m[2, 0]) / s),
        )
    s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
    return (
        float((m[0, 2] + m[2, 0]) / s),
        float((m[1, 2] + m[2, 1]) / s),
        float(0.25 * s),
        float((m[1, 0] - m[0, 1]) / s),
    )
