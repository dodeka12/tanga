# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the delta-encoded animation recording.

The animated HTML export stores frame 0 as a full snapshot and each later frame
as only the entities that changed or were removed.  This covers the Python side:
``diff_entity_frames`` and ``AnimationRecording.to_diff_dict``, including a
lossless round-trip.
"""

import base64
import gzip
import json
import math
import re
from typing import Any

from pytanga.geometry import Circle, Point
from pytanga.viz import AnimStyle, PointPath, PointPathStyle, Visualizer
from pytanga.viz.export._animated_figure import render_export_animated_html
from pytanga.viz.export._animation_recording import (
    AnimationRecording,
    diff_entity_frames,
)
from pytanga.viz.scene import Scene


def _expand(
    initial: list[dict[str, Any]],
    deltas: list[dict[str, Any]],
) -> list[list[dict[str, Any]]]:
    """Python mirror of the JS ``_expandFrames`` (see the plan contract)."""
    frames = [list(initial)]
    state = {ent["id"]: ent for ent in initial}
    for d in deltas:
        for eid in d.get("remove", []):
            state.pop(eid, None)
        for ent in d.get("set", []):
            state[ent["id"]] = ent
        frames.append(list(state.values()))
    return frames


def _ent(eid: str, kind: str, **extra: object) -> dict[str, object]:
    ent = {"id": eid, "kind": kind, "layer": "scene"}
    ent.update(extra)
    return ent


def test_diff_static_entity_stored_once() -> None:
    static = _ent("s", "PointPath", points=[[0, 0, 0], [1, 0, 0]])
    frames = [
        [static, _ent("m", "Point", pos=0)],
        [static, _ent("m", "Point", pos=1)],
        [static, _ent("m", "Point", pos=2)],
    ]

    initial, deltas = diff_entity_frames(frames)

    assert initial == frames[0]
    assert [d["set"] for d in deltas] == [
        [_ent("m", "Point", pos=1)],
        [_ent("m", "Point", pos=2)],
    ]
    assert all(d["remove"] == [] for d in deltas)
    assert all(e["id"] != "s" for d in deltas for e in d["set"])


def test_diff_added_and_removed() -> None:
    frames = [
        [_ent("a", "Point", pos=0), _ent("b", "Point", pos=0)],
        [_ent("a", "Point", pos=1), _ent("c", "Point", pos=0)],
    ]

    initial, deltas = diff_entity_frames(frames)

    assert initial == frames[0]
    assert deltas[0]["remove"] == ["b"]
    assert sorted(e["id"] for e in deltas[0]["set"]) == ["a", "c"]


def test_diff_empty() -> None:
    assert diff_entity_frames([]) == ([], [])


def test_diff_roundtrip_lossless() -> None:
    static = _ent("s", "PointPath", points=[[0, 0, 0], [1, 0, 0], [2, 0, 0]])
    frames = [
        [static, _ent("m", "Point", pos=0)],
        [static, _ent("m", "Point", pos=1)],
        [static, _ent("m", "Point", pos=2), _ent("c", "Circle", radius=1.0)],
        [static, _ent("m", "Point", pos=3), _ent("c", "Circle", radius=2.0)],
        [static, _ent("m", "Point", pos=4)],
    ]

    initial, deltas = diff_entity_frames(frames)
    assert _expand(initial, deltas) == frames


def test_to_diff_dict_shape() -> None:
    scene = Scene()
    eid = scene.add(Point(0, 0, 0))
    rec = AnimationRecording(scene)
    rec.capture_frame()
    scene.update_entity(eid, Point(5, -3, 2))
    rec.capture_frame()

    data = rec.to_diff_dict()
    assert set(data) == {
        "initial",
        "deltas",
        "frame_count",
        "cameras",
        "assets",
        "frame_assets",
    }
    assert "frames" not in data
    assert data["frame_count"] == 2
    assert _expand(data["initial"], data["deltas"]) == rec.frames


def _recording() -> AnimationRecording:
    scene = Scene()
    eid = scene.add(Point(0, 0, 0))
    rec = AnimationRecording(scene)
    rec.capture_frame()
    scene.update_entity(eid, Point(1, 2, 3))
    rec.capture_frame()
    return rec


def test_render_diff_html_embeds_expand() -> None:
    html = render_export_animated_html(_recording().to_diff_dict())
    assert "_expandFrames" in html
    assert "const frames = _expandFrames(animData);" in html
    assert '"deltas"' in html


def test_render_legacy_frames_still_works() -> None:
    html = render_export_animated_html(_recording().to_dict())
    assert "_expandFrames" in html
    assert '"frames"' in html


def test_render_diff_html_roundtrips() -> None:
    rec = _recording()
    html = render_export_animated_html(rec.to_diff_dict())

    match = re.search(r"window\.__TANGA_ANIMATION__ = (\{.*\})", html)
    assert match is not None
    data = json.loads(match.group(1))
    assert {"initial", "deltas"} <= set(data)
    assert "frames" not in data
    assert _expand(data["initial"], data["deltas"]) == rec.frames


def _static_path_recording() -> tuple[AnimationRecording, str]:
    """Record a static ``PointPath`` + moving/pulsing circles; return (rec, path_id)."""
    viz = Visualizer(add_default_axes=False, add_default_grid=False)

    orbit = PointPath(max_points=16)
    for i in range(16):
        angle = 2.0 * math.pi * i / 16
        orbit.add((4.0 * math.cos(angle), 4.0 * math.sin(angle), 0.0))
    path_ref = viz.new(orbit, style=PointPathStyle(line_thickness=1))

    moving = viz.new(Circle(center=Point(4.0, 0.0, 0.0), radius=0.3))
    pulsing = viz.new(Circle(center=Point(0.0, 0.0, 0.0), radius=1.0))
    viz.flush()

    rec = viz.start_animation_recording()
    for frame in range(20):
        angle = 2.0 * math.pi * frame / 20
        moving.entity = Circle(
            center=Point(4.0 * math.cos(angle), 4.0 * math.sin(angle), 0.0),
            radius=0.3,
        )
        pulsing.entity = Circle(
            center=Point(0.0, 0.0, 0.0),
            radius=1.0 + 0.6 * math.sin(2.0 * angle),
        )
        viz.flush()
        rec.capture_frame()

    return rec, path_ref.id


def _decompress_embedded_data(html: str) -> dict:
    match = re.search(
        r'<script type="application/octet-stream" id="tanga-anim-data">\s*'
        r"([A-Za-z0-9+/=]+)\s*</script>",
        html,
    )
    assert match is not None
    raw = gzip.decompress(base64.b64decode(match.group(1)))
    return json.loads(raw.decode("utf-8"))


def test_end_to_end_diff_payload_decompresses() -> None:
    rec, _ = _static_path_recording()
    html = render_export_animated_html(rec.to_diff_dict(), anim_style={"compress": True})

    data = _decompress_embedded_data(html)
    assert {"initial", "deltas"} <= set(data)
    assert "frames" not in data
    assert data["frame_count"] == 20
    assert len(data["deltas"]) == 19


def test_static_path_stored_once() -> None:
    rec, path_id = _static_path_recording()
    html = render_export_animated_html(rec.to_diff_dict(), anim_style={"compress": True})
    data = _decompress_embedded_data(html)

    initial_ids = [e["id"] for e in data["initial"]]
    assert initial_ids.count(path_id) == 1
    for delta in data["deltas"]:
        assert all(e["id"] != path_id for e in delta["set"])


def _id_map(frame: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {e["id"]: e for e in frame}


def test_diff_payload_lossless_and_smaller() -> None:
    rec, _ = _static_path_recording()
    html = render_export_animated_html(rec.to_diff_dict(), anim_style={"compress": True})
    data = _decompress_embedded_data(html)

    expanded = _expand(data["initial"], data["deltas"])
    normalized = json.loads(json.dumps(rec.frames))
    assert len(expanded) == len(normalized)
    for exp_frame, norm_frame in zip(expanded, normalized):
        assert _id_map(exp_frame) == _id_map(norm_frame)

    full_json = json.dumps(rec.to_dict(), separators=(",", ":"))
    diff_json = json.dumps(rec.to_diff_dict(), separators=(",", ":"))
    assert len(diff_json) < len(full_json) * 0.5
