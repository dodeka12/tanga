# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for CameraConfig, SceneConfig, Scene, and Visualizer basics."""

import json
import threading

import pytest
from pytanga.geometry.entities import Point
from pytanga.viz._props import _normalize_color
from pytanga.viz._scene_objects import Axes2D, Axes3D, Axis, Grid
from pytanga.viz.camera import CameraConfig2d, CameraConfig3d
from pytanga.viz.camera import (
    View2DConfig,
    View3dConfig,
    get_camera,
    get_camera_view2d,
    get_camera_view3d,
)
from pytanga.viz.scene import Scene, SceneConfig, SceneObject
from pytanga.viz.serializer import serialize_entity
from pytanga.viz.visualizer import Visualizer

# ── CameraConfig ────────────────────────────────────────────


class TestCameraConfig:
    def test_camera3d_type(self):
        c = CameraConfig3d()
        assert c.type == "3d"
        assert c.fov == 50.0

    def test_camera2d_type(self):
        c = CameraConfig2d(xmin=0.0, xmax=2.0, ymin=0.0, ymax=1.0)
        assert c.type == "2d"
        assert c.uniform is True
        assert c.border_px == 0.0

    def test_camera3d_to_dict_omits_none(self):
        c = CameraConfig3d()
        d = c.to_dict()
        assert d == {"type": "3d", "fov": 50.0}

    def test_camera3d_to_dict_partial(self):
        c = CameraConfig3d(position=(1, 2, 3), fov=45)
        d = c.to_dict()
        assert d == {"type": "3d", "position": [1, 2, 3], "fov": 45}

    def test_camera3d_to_dict_full(self):
        c = CameraConfig3d(
            position=(10, 6, 12),
            target=(0, 0, 0),
            fov=50,
            near=0.1,
            far=200,
        )
        d = c.to_dict()
        assert d["type"] == "3d"
        assert d["position"] == [10, 6, 12]
        assert d["target"] == [0, 0, 0]
        assert d["fov"] == 50
        assert d["near"] == 0.1
        assert d["far"] == 200

    def test_camera2d_to_dict(self):
        c = CameraConfig2d(xmin=-1.0, xmax=1.0, ymin=-2.0, ymax=2.0)
        d = c.to_dict()
        assert d == {
            "type": "2d",
            "xmin": -1.0,
            "xmax": 1.0,
            "ymin": -2.0,
            "ymax": 2.0,
            "uniform": True,
            "border_px": 0.0,
        }

    def test_json_serializable(self):
        json.dumps(CameraConfig3d(position=(1, 2, 3), fov=45).to_dict())
        json.dumps(CameraConfig2d(xmin=0, xmax=1, ymin=0, ymax=1).to_dict())


class TestCameraBuilders:
    def test_view2d_builder(self):
        cam = get_camera_view2d(
            View2DConfig(xmin=0.0, xmax=4.0, ymin=0.0, ymax=3.0, border_world=1.0)
        )
        assert isinstance(cam, CameraConfig2d)
        assert cam.xmin == -1.0
        assert cam.xmax == 5.0
        assert cam.ymin == -1.0
        assert cam.ymax == 4.0
        assert cam.position == (2.0, 1.5, 20.0)
        assert cam.target == (2.0, 1.5, 0.0)
        assert cam.uniform is True
        assert cam.border_px == 0.0

    def test_view3d_builder(self):
        cam = get_camera_view3d(View3dConfig((0, 0, 0), (0, 0, 1), 6.0, 5.0))
        assert isinstance(cam, CameraConfig3d)
        assert cam.fov == 50.0
        assert cam.target == (0, 0, 0)
        # position is along +Z at a positive distance
        assert cam.position is not None
        assert cam.position[2] > 0
        # up defaults to (0, 1, 0) so orbit behaviour matches the no-camera case
        assert cam.up == (0.0, 1.0, 0.0)
        # the resulting config is a plain projective 3D camera with no
        # plane-fit extent fields — the frontend renders it with free
        # orbit controls (rotation + pan).
        assert not hasattr(cam, "extent_u")
        assert not hasattr(cam, "extent_v")

    def test_view3d_explicit_has_no_extents(self):
        cam = CameraConfig3d(position=(10, 6, 12), target=(0, 0, 0), fov=50)
        assert not hasattr(cam, "extent_u")
        assert not hasattr(cam, "extent_v")
        assert cam.position == (10, 6, 12)

    def test_view3d_custom_up_passthrough(self):
        cam = get_camera_view3d(
            View3dConfig((0, 0, 0), (0, 0, 1), 6.0, 5.0, up=(0.2, 0.3, 1.0))
        )
        assert cam.up == (0.2, 0.3, 1.0)

    def test_get_camera_dispatches(self):
        assert isinstance(get_camera(View2DConfig(xmin=0, xmax=1, ymin=0, ymax=1)), CameraConfig2d)
        assert isinstance(
            get_camera(View3dConfig((0, 0, 0), (0, 0, 1), 6.0, 5.0)),
            CameraConfig3d,
        )

    def test_get_camera_rejects_unknown(self):
        with pytest.raises(TypeError):
            get_camera(object())  # type: ignore[arg-type]


# ── SceneConfig ─────────────────────────────────────────────


class TestSceneConfig:
    def test_defaults(self):
        sc = SceneConfig()
        assert sc.background_color == "#1a1a2e"
        assert sc.camera is None

    def test_to_dict_includes_type(self):
        sc = SceneConfig()
        d = sc.to_dict()
        assert d["type"] == "scene_config"
        assert "camera" not in d  # None camera should be omitted

    def test_to_dict_omits_obsolete_keys(self):
        sc = SceneConfig()
        d = sc.to_dict()
        assert "space_extent" not in d
        assert "show_grid" not in d
        assert "show_axes" not in d

    def test_to_dict_with_camera(self):
        sc = SceneConfig(camera=CameraConfig3d(fov=30))
        d = sc.to_dict()
        assert d["camera"] == {"type": "3d", "fov": 30}

    def test_json_serializable(self):
        sc = SceneConfig(camera=CameraConfig3d(position=(1, 2, 3)))
        json.dumps(sc.to_dict())  # should not raise


# ── SceneObject ────────────────────────────────────────────


class TestSceneObject:
    def test_defaults(self):
        obj = SceneObject(id="abc", kind="Point")
        assert obj.id == "abc"
        assert obj.kind == "Point"
        assert obj.layer == "scene"
        assert obj.properties == {}
        assert obj.dirty is True

    def test_custom_layer(self):
        obj = SceneObject(id="l1", layer="overlay", kind="label")
        assert obj.layer == "overlay"


# ── Scene ──────────────────────────────────────────────────


class TestScene:
    def test_add_entity(self):
        s = Scene()
        eid = s.add(Point(1, 2, 3))
        assert isinstance(eid, str)
        assert len(eid) == 8  # UUID8
        assert s.entity_count == 1

    def test_add_generates_unique_ids(self):
        s = Scene()
        id1 = s.add(Point(1, 2, 3))
        id2 = s.add(Point(4, 5, 6))
        assert id1 != id2

    def test_flush_returns_new_entities(self):
        s = Scene()
        s.add(Point(1, 0, 0))
        dirty, removed = s.flush()
        assert len(dirty) == 1
        assert dirty[0]["aspect"] == "full"
        assert dirty[0]["value"]["kind"] == "Point"
        assert removed == []

    def test_flush_only_returns_dirty(self):
        s = Scene()
        s.add(Point(1, 0, 0))
        s.flush()
        dirty, _ = s.flush()
        assert dirty == []

    def test_update_marks_dirty(self):
        s = Scene()
        eid = s.add(Point(0, 0, 0))
        s.flush()
        s.update(eid, color="#ff0000")
        dirty, _ = s.flush()
        assert len(dirty) == 1

    def test_update_entity_replaces_geometry(self):
        s = Scene()
        eid = s.add(Point(1, 0, 0))
        s.flush()  # consume the initial "full" dirty flag
        s.update_entity(eid, Point(5, 6, 7))
        dirty, _ = s.flush()
        assert dirty[0]["aspect"] == "content"
        assert dirty[0]["value"]["position"] == [5, 6, 7]

    def test_new_node_with_transform_mutation_still_full(self):
        # A node that has never reached the client must emit `full` even if a
        # sub-aspect (transform) is mutated before the first flush; otherwise
        # the client never learns about the node (regression for nested groups).
        s = Scene()
        g = s.add_group("arm")
        g.set_transform(position=(1, 0, 0))
        dirty, _ = s.flush()
        patches = [p for p in dirty if p["id"] == g.id]
        assert [p["aspect"] for p in patches] == ["full"]
        assert patches[0]["value"]["transform"]["position"] == [1, 0, 0]

    def test_remove_then_flush(self):
        s = Scene()
        eid = s.add(Point(0, 0, 0))
        s.remove(eid)
        dirty, removed = s.flush()
        assert eid in removed

    def test_clear_then_flush(self):
        s = Scene()
        s.add(Point(0, 0, 0))
        s.add(Point(1, 1, 1))
        s.clear()
        _, removed = s.flush()
        assert len(removed) == 2

    def test_full_state(self):
        s = Scene()
        s.add(Point(1, 0, 0))
        s.add(Point(0, 1, 0))
        state = s.full_state()
        assert len(state) == 2

    def test_add_with_explicit_id(self):
        s = Scene()
        eid = s.add(Point(1, 2, 3), entity_id="custom_123")
        assert eid == "custom_123"

    def test_add_label(self):
        from pytanga.viz._label import Label

        s = Scene()
        lbl = Label(text="test", position=(0, 0, 0))
        lid = s.add_label(lbl)
        assert isinstance(lid, str)
        labels = [o for o in s.full_state() if o.get("kind") == "label"]
        assert len(labels) == 1
        assert labels[0]["text"] == "test"


# ── Visualizer Basics ──────────────────────────────────────


class TestVisualizer:
    def test_default_construction(self):
        viz = Visualizer()
        assert viz._port == 8765
        assert viz._host == "localhost"

    def test_animate_yields_frames_and_stops_on_shutdown(self, monkeypatch):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        # Pretend the server is already running so animate() skips start().
        viz._server = object()
        viz._shutdown_requested = threading.Event()
        monkeypatch.setattr(viz, "stop", lambda: None)

        gen = viz.animate(fps=0)  # fps=0 → no pacing
        assert next(gen) >= 0.0
        assert next(gen) >= 0.0

        viz._shutdown_requested.set()
        with pytest.raises(StopIteration):
            next(gen)

    def test_opns_kwarg_rejected(self):
        with pytest.raises(TypeError):
            Visualizer(opns=False)

    def test_custom_port_and_host(self):
        viz = Visualizer(port=9999, host="127.0.0.1")
        assert viz._port == 9999
        assert viz._host == "127.0.0.1"

    def test_obsolete_kwargs_rejected(self):
        with pytest.raises(TypeError):
            Visualizer(space_extent=25)
        with pytest.raises(TypeError):
            Visualizer(show_grid=False)
        with pytest.raises(TypeError):
            Visualizer(show_axes=False)

    def test_camera_config_forwarded(self):
        cam = CameraConfig3d(fov=35)
        viz = Visualizer(camera=cam)
        assert viz._config.camera is cam

    def test_camera_accepts_view2d_config(self):
        viz = Visualizer(camera=View2DConfig(xmin=0, xmax=2, ymin=0, ymax=1))
        cam = viz._config.camera
        assert isinstance(cam, CameraConfig2d)
        assert cam.xmin == 0.0
        assert cam.xmax == 2.0

    def test_camera_accepts_view3d_config(self):
        viz = Visualizer(camera=View3dConfig((0, 0, 0), (0, 0, 1), 6.0, 5.0))
        cam = viz._config.camera
        assert isinstance(cam, CameraConfig3d)
        assert cam.position is not None
        assert cam.target == (0, 0, 0)
        assert not hasattr(cam, "extent_u")
        assert not hasattr(cam, "extent_v")

    def test_space_dim_deduced_from_view2d(self):
        viz = Visualizer(camera=View2DConfig(xmin=0, xmax=2, ymin=0, ymax=1))
        assert viz._config.space_dim == 2
        assert viz._config.title == "Tanga 2D Viewer"

    def test_space_dim_deduced_from_view3d(self):
        viz = Visualizer(camera=View3dConfig((0, 0, 0), (0, 0, 1), 6.0, 5.0))
        assert viz._config.space_dim == 3

    def test_space_dim_explicit_overrides_camera(self):
        viz = Visualizer(camera=View2DConfig(xmin=0, xmax=2, ymin=0, ymax=1), space_dim=3)
        assert viz._config.space_dim == 3

    def test_add_entity_returns_id(self):
        viz = Visualizer()
        eid = viz.add(Point(1, 2, 3))
        assert isinstance(eid, str)

    def test_add_with_color_normalizes(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add(Point(1, 2, 3), color=(1.0, 0.5, 0.0))
        state = viz._scene.full_state()
        assert state[0]["color"] == "#ff8000"

    def test_add_with_4tuple_extracts_opacity(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add(Point(1, 2, 3), color=(1.0, 0.0, 0.0, 0.3))
        state = viz._scene.full_state()
        assert state[0]["color"] == "#ff0000"
        assert state[0]["opacity"] == 0.3

    def test_add_with_color_and_explicit_opacity(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add(Point(1, 2, 3), color=(1.0, 0.0, 0.0, 0.3), opacity=0.8)
        state = viz._scene.full_state()
        assert state[0]["color"] == "#ff0000"
        assert state[0]["opacity"] == 0.8  # explicit wins

    def test_add_with_hex_color_passthrough(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add(Point(0, 0, 0), color="#abcdef")
        state = viz._scene.full_state()
        assert state[0]["color"] == "#abcdef"

    def test_add_with_style(self):
        from pytanga.viz._styles import PointStyle

        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add(Point(0, 0, 0), style=PointStyle(size=0.5, color="#00ff00"))
        state = viz._scene.full_state()
        assert state[0]["style"]["size"] == 0.5
        assert state[0]["style"]["color"] == "#00ff00"

    def test_update_with_color(self):
        viz = Visualizer()
        eid = viz.add(Point(0, 0, 0))
        viz._scene.flush()
        viz.update(eid, color="#00ff00")
        dirty, _ = viz._scene.flush()
        assert dirty[0]["aspect"] == "style"
        assert dirty[0]["value"]["style"]["color"] == "#00ff00"

    def test_remove_delegates(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        eid = viz.add(Point(0, 0, 0))
        viz.remove(eid)
        assert viz._scene.entity_count == 1  # until flush
        viz._scene.flush()
        assert viz._scene.entity_count == 0

    def test_clear_delegates(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add(Point(0, 0, 0))
        viz.add(Point(1, 1, 1))
        viz.clear()
        assert viz._scene.entity_count == 2  # until flush
        viz._scene.flush()
        assert viz._scene.entity_count == 0

    def test_server_methods_exist(self):
        """start/stop/flush/run are callable (server lifecycle)."""
        viz = Visualizer()
        assert callable(viz.start)
        assert callable(viz.stop)
        assert callable(viz.flush)
        assert callable(viz.run)

    def test_main_scene_property(self):
        viz = Visualizer()
        assert isinstance(viz.main_scene, Scene)

    def test_default_styles_accessible(self):
        viz = Visualizer()
        from pytanga.geometry import Sphere

        assert "Sphere" in viz.styles.kind
        assert viz.styles[Sphere].wireframe is True
        assert viz.styles[Sphere].opacity == 0.4

    def test_set_default_color_via_styles(self):
        viz = Visualizer()
        viz.set_default_color("point", "#00ff00")
        assert viz.styles["Point"].color == "#00ff00"

    def test_set_default_color_rgba_sets_opacity_too(self):
        viz = Visualizer()
        viz.set_default_color("point", (1.0, 0.0, 0.0, 0.3))
        assert viz.styles["Point"].color == "#ff0000"
        assert viz.styles["Point"].opacity == 0.3

    def test_set_default_color_unknown_kind_raises(self):
        viz = Visualizer()
        with pytest.raises(ValueError, match="Unknown entity kind"):
            viz.set_default_color("banana", "#fff")


# ── _normalize_color ──────────────────────────────────────


class TestNormalizeColor:
    def test_hex_passthrough(self):
        assert _normalize_color("#ff4444") == "#ff4444"

    def test_rgb_tuple(self):
        assert _normalize_color((1.0, 0.0, 0.0)) == "#ff0000"
        assert _normalize_color((0.0, 1.0, 0.0)) == "#00ff00"
        assert _normalize_color((0.0, 0.0, 1.0)) == "#0000ff"

    def test_rgba_tuple_returns_hex_and_alpha(self):
        result = _normalize_color((1.0, 0.0, 0.0, 0.5))
        assert isinstance(result, tuple)
        assert result[0] == "#ff0000"
        assert result[1] == 0.5

    def test_clamping(self):
        result = _normalize_color((2.0, -1.0, 0.5))
        assert result == "#ff0080"

    def test_fractional(self):
        result = _normalize_color((0.2, 0.4, 0.6))
        assert isinstance(result, str)
        assert result.startswith("#")
        assert len(result) == 7

    def test_invalid_tuple_length_raises(self):
        with pytest.raises(ValueError, match="3 or 4"):
            _normalize_color((1.0,))  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="3 or 4"):
            _normalize_color((1.0, 2.0, 3.0, 4.0, 5.0))  # type: ignore[arg-type]

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError, match="str or tuple"):
            _normalize_color(123)  # type: ignore[arg-type]


# ── Label style defaults ──────────────────────────────────


class TestLabelDefaults:
    def test_label_style_defaults(self):
        from pytanga.viz._styles import LabelStyle

        ls = LabelStyle()
        assert ls.font_size is None
        assert ls.font_family is None
        assert ls.color is None
        assert ls.background is None
        assert ls.offset_local is None
        assert ls.offset_2d is None
        assert ls.align is None

    def test_point_label_aligns_top_left(self):
        from pytanga.geometry import Line, Point

        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add(Point(0, 0, 0), label="P")
        viz.add(Line.from_points(Point(0, 0, 0), Point(1, 0, 0)), label="L")
        labels = {
            o.get("text"): o["style"]
            for o in viz._scene.full_state()
            if o.get("kind") == "label"
        }
        assert labels["P"]["align"] == [0.0, 0.0]
        assert labels["P"]["offset_2d"] == [5.0, 5.0]
        # Non-point labels keep the centered default.
        assert labels["L"]["align"] == [0.5, 0.5]
        assert labels["L"]["offset_2d"] == [0.0, 0.0]

    def test_label_style_along_and_rotation_to_dict(self):
        from pytanga.viz._styles import LabelStyle

        assert LabelStyle(along=0.5, rotation=45).to_dict()["along"] == 0.5
        assert LabelStyle(along=0.5, rotation=45).to_dict()["rotation"] == 45
        assert LabelStyle(along=(0.25, 0.5)).to_dict()["along"] == [0.25, 0.5]

    def test_line_label_default_along(self):
        from pytanga.viz._style_dict import _make_default_label_styles

        styles = _make_default_label_styles()
        assert styles["Line"].along == 0.5
        assert styles["Sphere"].along is None

    def test_label_serialization_strips_along_keeps_rotation(self):
        from pytanga.geometry import Point
        from pytanga.viz._styles import LabelStyle

        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add(Point(0, 0, 0), label="P", label_style=LabelStyle(rotation=45, along=0.5))
        labels = [o for o in viz._scene.full_state() if o.get("kind") == "label"]
        assert len(labels) == 1
        assert "along" not in labels[0]["style"]
        assert labels[0]["style"]["rotation"] == 45

    def test_default_label_styles_accepts_class_key(self):
        from pytanga.geometry import Sphere
        from pytanga.viz._styles import LabelStyle

        viz = Visualizer()
        viz.styles.label_kind[Sphere] = LabelStyle(font_size=18)
        assert viz.styles.label_kind["Sphere"].font_size == 18

    def test_default_label_style_setter(self):
        from pytanga.viz._styles import LabelStyle

        viz = Visualizer()
        viz.styles.label_base = LabelStyle(font_size=22)
        assert viz.styles.label_base.font_size == 22

    def test_default_label_styles_resolution(self):
        from pytanga.geometry import Sphere
        from pytanga.viz._styles import LabelStyle

        viz = Visualizer()
        viz.styles.label_kind["Sphere"] = LabelStyle(font_size=18)
        eid = viz.add(Sphere(Point(0, 0, 0), 1.0), label="S")
        labels = [o for o in viz._scene.full_state() if o.get("kind") == "label"]
        assert len(labels) == 1
        assert labels[0]["style"]["font_size"] == 18
        assert eid


class TestStyleDictMerge:
    def test_merge_preserves_unset_fields(self):
        from pytanga.viz._styles import SphereStyle

        viz = Visualizer()
        original = viz.styles["Sphere"].opacity
        viz.styles.kind.merge("Sphere", SphereStyle(color="#00ff00"))
        s = viz.styles["Sphere"]
        assert s.color == "#00ff00"
        assert s.opacity == original

    def test_merge_accepts_class_key(self):
        from pytanga.geometry import Sphere
        from pytanga.viz._styles import SphereStyle

        viz = Visualizer()
        viz.styles.kind.merge(Sphere, SphereStyle(opacity=0.9))
        assert viz.styles["Sphere"].opacity == 0.9

    def test_setitem_is_full_replacement(self):
        from pytanga.viz._styles import SphereStyle

        viz = Visualizer()
        viz.styles["Sphere"] = SphereStyle(color="#00ff00")
        s = viz.styles["Sphere"]
        assert s.opacity is None  # lost, not merged

    def test_merge_shallow_replaces_nested(self):
        from pytanga.viz._styles import DashedWireframe, SphereStyle, TextureLabelStyle

        viz = Visualizer()
        viz.styles.kind.merge(
            "Sphere",
            SphereStyle(texture_label=TextureLabelStyle(font_size=30)),
            deep=False,
        )
        tl = viz.styles["Sphere"].texture_label
        assert tl.font_size == 30
        assert tl.offset_v is None
        assert tl.repeat_u is None

    def test_merge_deep_preserves_nested(self):
        from pytanga.viz._styles import SphereStyle, TextureLabelStyle

        viz = Visualizer()
        viz.styles.kind.merge(
            "Sphere",
            SphereStyle(texture_label=TextureLabelStyle(font_size=30)),
            deep=True,
        )
        tl = viz.styles["Sphere"].texture_label
        assert tl.font_size == 30

    def test_label_merge_has_full_base(self):
        from pytanga.viz._styles import LabelStyle

        viz = Visualizer()
        viz.styles.label_kind.merge("Point", LabelStyle(font_size=20))
        ls = viz.styles.label_kind["Point"]
        assert ls.font_size == 20
        assert ls.color is not None


# ── Axis / Grid serialization ──────────────────────────────


class TestAxisSerialization:
    def test_axis_serialization(self):
        ent = Axis((0, 0, 0), (3, 0, 0), major_interval=1.0, label="X")
        d = serialize_entity(ent, "a1", kind="Axis")
        assert d["kind"] == "Axis"
        assert d["start"] == [0, 0, 0]
        assert d["end"] == [3, 0, 0]
        assert d["majorInterval"] == 1.0
        assert d["label"] == "X"
        assert d["labelFormat"] == ".1f"
        assert d["showTicks"] is True

    def test_axis_minor_interval_omitted_when_none(self):
        ent = Axis((0, 0, 0), (3, 0, 0))
        d = serialize_entity(ent, "a1", kind="Axis")
        assert "minorInterval" not in d


class TestGridSerialization:
    def test_grid_serialization(self):
        g = Grid(range_u=(-5.0, 5.0), range_v=(-3.0, 3.0))
        d = serialize_entity(g, "g1", kind="Grid")
        assert d["kind"] == "Grid"
        assert d["origin"] == [0.0, 0.0, -1.0]
        assert d["dir_u"] == [1.0, 0.0, 0.0]
        assert d["dir_v"] == [0.0, 1.0, 0.0]
        assert d["range_u"] == [-5.0, 5.0]
        assert d["range_v"] == [-3.0, 3.0]

    def test_grid_asymmetric_ranges(self):
        g = Grid(range_u=(-2.0, 3.0), range_v=(-1.0, 4.0))
        d = serialize_entity(g, "g2", kind="Grid")
        assert d["range_u"] == [-2.0, 3.0]
        assert d["range_v"] == [-1.0, 4.0]


class TestAxesSerialization:
    def test_axes2d_single_object_kind(self):
        from pytanga.viz import Axes2DStyle, AxisStyle

        a = Axes2D(range_u=(-2, 3), range_v=(-1, 2), labels=("X", "Y"))
        d = serialize_entity(
            a, "ax2", kind="Axes2D",
            properties={"style": Axes2DStyle(u=AxisStyle(color="#ff0000"), v=AxisStyle(color="#00ff00"))},
        )
        assert d["kind"] == "Axes2D"
        assert d["origin"] == [0.0, 0.0, -0.5]
        assert "axes" in d
        # u: positive + negative halves (both red), v: positive + negative (both green)
        entries = d["axes"]
        assert len(entries) == 4
        by_end = {tuple(e["end"]): e for e in entries}
        assert by_end[(3.0, 0.0, -0.5)]["color"] == "#ff0000"
        assert by_end[(-2.0, 0.0, -0.5)]["color"] == "#ff0000"
        assert by_end[(0.0, 2.0, -0.5)]["color"] == "#00ff00"
        assert by_end[(0.0, -1.0, -0.5)]["color"] == "#00ff00"

    def test_axes3d_per_direction_style(self):
        from pytanga.viz import Axes3DStyle, AxisStyle

        a = Axes3D(range_u=(0, 2), range_v=(0, 2), range_w=(0, 2), labels=("X", "Y", "Z"))
        d = serialize_entity(
            a, "ax3", kind="Axes3D",
            properties={"style": Axes3DStyle(
                u=AxisStyle(color="#ff0000"),
                v=AxisStyle(color="#00ff00"),
                w=AxisStyle(color="#0000ff"),
            )},
        )
        assert d["kind"] == "Axes3D"
        entries = d["axes"]
        assert len(entries) == 3
        by_end = {tuple(e["end"]): e for e in entries}
        assert by_end[(2.0, 0.0, 0.0)]["color"] == "#ff0000"
        assert by_end[(0.0, 2.0, 0.0)]["color"] == "#00ff00"
        assert by_end[(0.0, 0.0, 2.0)]["color"] == "#0000ff"

    def test_axes_sparse_axis_style_falls_back_to_axis_defaults(self):
        from pytanga.viz import Axes2DStyle, AxisStyle

        a = Axes2D(range_u=(0, 1), range_v=(0, 1))
        d = serialize_entity(
            a, "ax2", kind="Axes2D",
            properties={"style": Axes2DStyle(u=AxisStyle(color="#ff0000"), v=AxisStyle())},
        )
        entries = d["axes"]
        u_entry = entries[0]  # positive half of u, red
        v_entry = entries[1]  # positive half of v, sparse
        assert u_entry["color"] == "#ff0000"
        # sparse AxisStyle resolves to canonical Axis defaults
        assert v_entry["style"]["color"] == "#888888"
        assert v_entry["style"]["opacity"] == 1.0
        assert v_entry["style"]["line_thickness"] == 2.0

    def test_axes_without_style_uses_canonical_group(self):
        a = Axes2D(range_u=(0, 1), range_v=(0, 1))
        d = serialize_entity(a, "ax2", kind="Axes2D")
        entries = d["axes"]
        assert len(entries) == 2
        for e in entries:
            assert e["style"]["color"] == "#888888"
            assert e["style"]["opacity"] == 1.0

    def test_axes_scalar_axis_style_applies_to_all_directions(self):
        from pytanga.viz import AxisStyle

        a = Axes3D(range_u=(0, 1), range_v=(0, 1), range_w=(0, 1), labels=("X", "Y", "Z"))
        d = serialize_entity(a, "ax3", kind="Axes3D", properties={"style": AxisStyle(color="#ff0000")})
        entries = d["axes"]
        assert len(entries) == 3
        for e in entries:
            assert e["color"] == "#ff0000"

    def test_axes_label_style_flows_into_entries(self):
        from pytanga.viz import Axes2DStyle, AxisStyle, LabelStyle

        a = Axes2D(range_u=(0, 1), range_v=(0, 1))
        d = serialize_entity(
            a, "ax2", kind="Axes2D",
            properties={
                "style": Axes2DStyle(
                    u=AxisStyle(
                        label_at_major=False,
                        label_style=LabelStyle(font_size=20, align=(0.5, 0.0)),
                    ),
                    v=AxisStyle(label_style=LabelStyle(offset_2d=(3, 4))),
                )
            },
        )
        entries = d["axes"]
        u_entry = entries[0]
        v_entry = entries[1]
        assert u_entry["labelAtMajor"] is False
        assert u_entry["style"]["label_style"]["font_size"] == 20
        assert u_entry["style"]["label_style"]["align"] == [0.5, 0.0]
        assert v_entry["style"]["label_style"]["offset_2d"] == [3, 4]

    def test_axes_label_style_rotation_flows_into_entries(self):
        from pytanga.viz import Axes2DStyle, AxisStyle, LabelStyle

        a = Axes2D(range_u=(0, 1), range_v=(0, 1))
        d = serialize_entity(
            a, "ax2", kind="Axes2D",
            properties={
                "style": Axes2DStyle(
                    u=AxisStyle(label_style=LabelStyle(rotation=30)),
                    v=AxisStyle(label_style=LabelStyle(rotation=-20)),
                )
            },
        )
        entries = d["axes"]
        assert entries[0]["style"]["label_style"]["rotation"] == 30
        assert entries[1]["style"]["label_style"]["rotation"] == -20


class TestGridAxesStyles:
    def test_grid_style_defaults(self):
        from pytanga.viz import GridStyle

        s = GridStyle()
        assert s.color is None
        assert s.opacity is None
        assert s.line_thickness is None
        assert s.to_dict() == {"style_type": "GridStyle"}

    def test_axes_style_defaults(self):
        from pytanga.viz import AxisStyle

        s = AxisStyle()
        assert s.color is None
        assert s.opacity is None
        assert s.line_thickness is None
        assert s.label_at_major is None
        assert s.label_style is None
        assert s.to_dict() == {"style_type": "AxisStyle"}

    def test_axis_style_label_fields(self):
        from pytanga.viz import AxisStyle, LabelStyle

        s = AxisStyle(
            label_at_major=False,
            label_style=LabelStyle(font_size=18, align=(0.5, 0.0), offset_2d=(2, -4)),
        )
        d = s.to_dict()
        assert d["label_at_major"] is False
        assert d["label_style"] == {
            "style_type": "LabelStyle",
            "font_size": 18,
            "align": [0.5, 0.0],
            "offset_2d": [2, -4],
        }

    def test_axes2d_style_defaults(self):
        from pytanga.viz import Axes2DStyle, AxisStyle

        s = Axes2DStyle()
        assert isinstance(s.u, AxisStyle)
        assert isinstance(s.v, AxisStyle)
        d = s.to_dict()
        assert d["style_type"] == "Axes2DStyle"
        assert d["u"] == {"style_type": "AxisStyle"}
        assert d["v"] == {"style_type": "AxisStyle"}

    def test_axes3d_style_defaults(self):
        from pytanga.viz import Axes3DStyle, AxisStyle

        s = Axes3DStyle()
        assert isinstance(s.u, AxisStyle)
        assert isinstance(s.v, AxisStyle)
        assert isinstance(s.w, AxisStyle)
        assert s.to_dict()["style_type"] == "Axes3DStyle"

    def test_default_styles_registered(self):
        from pytanga.viz import Axes2DStyle, Axes3DStyle, AxisStyle, GridStyle

        viz = Visualizer()
        assert isinstance(viz.styles["Grid"], GridStyle)
        assert isinstance(viz.styles["Axis"], AxisStyle)
        assert isinstance(viz.styles["Axes2D"], Axes2DStyle)
        assert isinstance(viz.styles["Axes3D"], Axes3DStyle)
        assert viz.styles["Grid"].color == "#555555"
        assert viz.styles["Grid"].opacity == 0.8
        assert viz.styles["Grid"].line_thickness == 1.0
        assert viz.styles["Axis"].color == "#888888"
        assert viz.styles["Axis"].opacity == 1.0
        assert viz.styles["Axis"].line_thickness == 2.0

    def test_grid_style_via_add(self):
        from pytanga.viz import GridStyle

        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add(Grid(), style=GridStyle(color="#ff0000"))
        state = viz._scene.full_state()
        assert state[0]["color"] == "#ff0000"

    def test_axes_style_via_add(self):
        from pytanga.viz import AxisStyle

        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add(Axis((0, 0, 0), (1, 0, 0)), style=AxisStyle(color="#00ff00"))
        state = viz._scene.full_state()
        assert state[0]["color"] == "#00ff00"

    def test_grid_style_merge(self):
        from pytanga.viz import GridStyle

        viz = Visualizer()
        viz.styles.kind.merge("Grid", GridStyle(color="#00ff00"))
        assert viz.styles["Grid"].color == "#00ff00"
        assert viz.styles["Grid"].opacity == 0.8  # preserved

    def test_grid_set_default_color(self):
        viz = Visualizer()
        viz.set_default_color("grid", "#123456")
        assert viz.styles["Grid"].color == "#123456"


class TestAxesExpansion:
    def test_axes_3d_expands_to_three_axes(self):
        a = Axes3D(range_u=(0, 4), range_v=(0, 5), range_w=(0, 6), labels=("X", "Y", "Z"))
        axes = a.expand()
        assert len(axes) == 3
        assert [x.label for x in axes] == ["X", "Y", "Z"]
        assert axes[0].end == (4.0, 0.0, 0.0)
        assert axes[1].end == (0.0, 5.0, 0.0)
        assert axes[2].end == (0.0, 0.0, 6.0)

    def test_axes_2d_expands_to_two_axes(self):
        a = Axes2D(range_u=(0, 3), range_v=(0, 4), labels=("X", "Y"))
        axes = a.expand()
        assert len(axes) == 2
        assert [x.label for x in axes] == ["X", "Y"]
        assert axes[0].end == (3.0, 0.0, -0.5)
        assert axes[1].end == (0.0, 4.0, -0.5)

    def test_axes_2d_asymmetric_expands_to_four_axes(self):
        a = Axes2D(range_u=(-2.0, 3.0), range_v=(-1.0, 4.0), labels=("X", "Y"))
        axes = a.expand()
        assert len(axes) == 4
        # Order: u positive, u negative, v positive, v negative
        assert axes[0].end == (3.0, 0.0, -0.5)
        assert axes[0].label == "X"
        assert axes[0].value_step == 1.0
        assert axes[1].end == (-2.0, 0.0, -0.5)
        assert axes[1].label is None
        assert axes[1].value_step == -1.0
        assert axes[2].end == (0.0, 4.0, -0.5)
        assert axes[2].label == "Y"
        assert axes[2].value_step == 1.0
        assert axes[3].end == (0.0, -1.0, -0.5)
        assert axes[3].label is None
        assert axes[3].value_step == -1.0

    def test_axes_3d_asymmetric_expands_correctly(self):
        a = Axes3D(
            range_u=(-1.0, 2.0), range_v=(-2.0, 3.0), range_w=(0.0, 4.0),
            labels=("X", "Y", "Z"),
        )
        axes = a.expand()
        # u: 2 halves, v: 2 halves, w: 1 half
        assert len(axes) == 5
        assert axes[0].end == (2.0, 0.0, 0.0)
        assert axes[1].end == (-1.0, 0.0, 0.0)
        assert axes[3].end == (0.0, -2.0, 0.0)
        # w only positive (range_w=(0,4))
        assert axes[4].end == (0.0, 0.0, 4.0)
        assert axes[4].label == "Z"

    def test_axes_2d_origin_2d_padded_to_default_z(self):
        a = Axes2D(origin=(1.0, 2.0), range_u=(0, 1), range_v=(0, 1))
        axes = a.expand()
        assert axes[0].start == (1.0, 2.0, -0.5)

    def test_axes_2d_origin_3d_preserved(self):
        a = Axes2D(origin=(1.0, 2.0, 3.0), range_u=(0, 1), range_v=(0, 1))
        axes = a.expand()
        assert axes[0].start == (1.0, 2.0, 3.0)

    def test_grid_origin_2d_padded_behind(self):
        g = Grid(origin=(1.0, 2.0))
        assert g.origin == (1.0, 2.0, -1.0)

    def test_grid_origin_3d_preserved(self):
        g = Grid(origin=(1.0, 2.0, 3.0))
        assert g.origin == (1.0, 2.0, 3.0)

    def test_axis_value_step_serialization(self):
        ent = Axis((0, 0, 0), (-10, 0, 0), value_step=-1.0)
        d = serialize_entity(ent, "a1", kind="Axis")
        assert d["valueStep"] == -1.0
        assert "valueStart" not in d


# ── Default scene objects ──────────────────────────────────


class TestDefaultSceneObjects:
    def _kinds(self, viz):
        return sorted(o.kind for o in viz._scenes[""]._objects.values())

    def test_defaults_added_eagerly(self):
        viz = Visualizer()
        kinds = self._kinds(viz)
        assert "Axes3D" in kinds
        assert "Grid" in kinds

    def test_add_default_axes_false(self):
        viz = Visualizer(add_default_axes=False)
        kinds = self._kinds(viz)
        assert "Axes3D" not in kinds
        assert "Grid" in kinds

    def test_add_default_grid_false(self):
        viz = Visualizer(add_default_grid=False)
        kinds = self._kinds(viz)
        assert "Axes3D" in kinds
        assert "Grid" not in kinds

    def test_both_defaults_disabled(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        assert self._kinds(viz) == []

    def test_defaults_authoritative_with_custom_camera(self):
        viz = Visualizer(camera=View3dConfig((0, 0, 0), (0, 0, 1), 6.0, 5.0))
        kinds = self._kinds(viz)
        assert "Axes3D" in kinds
        assert "Grid" in kinds

    def test_user_axes_in_addition_to_defaults(self):
        viz = Visualizer()
        viz.add(Axis((0, 0, 0), (1, 0, 0)))
        kinds = self._kinds(viz)
        assert "Axis" in kinds
        assert "Axes3D" in kinds
        assert "Grid" in kinds
