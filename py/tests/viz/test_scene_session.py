# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for CameraConfig, SceneConfig, Scene, and Visualizer basics."""

import json

import pytest
from pytanga.geometry.entities import Point
from pytanga.viz._props import _normalize_color
from pytanga.viz._scene_objects import Axes2D, Axes3D, Axis, Grid
from pytanga.viz.scene import (
    CameraConfig,
    Scene,
    SceneConfig,
    SceneObject,
    View2DConfig,
    ViewPlaneConfig,
)
from pytanga.viz.serializer import serialize_entity
from pytanga.viz.visualizer import Visualizer

# ── CameraConfig ────────────────────────────────────────────


class TestCameraConfig:
    def test_all_none_by_default(self):
        c = CameraConfig()
        assert c.position is None
        assert c.target is None
        assert c.fov is None
        assert c.near is None
        assert c.far is None

    def test_to_dict_all_none_returns_empty(self):
        c = CameraConfig()
        assert c.to_dict() == {}

    def test_to_dict_partial(self):
        c = CameraConfig(position=(1, 2, 3), fov=45)
        d = c.to_dict()
        assert d == {"position": [1, 2, 3], "fov": 45}

    def test_to_dict_full(self):
        c = CameraConfig(
            position=(10, 6, 12),
            target=(0, 0, 0),
            fov=50,
            near=0.1,
            far=200,
        )
        d = c.to_dict()
        assert d["position"] == [10, 6, 12]
        assert d["target"] == [0, 0, 0]
        assert d["fov"] == 50
        assert d["near"] == 0.1
        assert d["far"] == 200

    def test_json_serializable(self):
        c = CameraConfig(position=(1, 2, 3), fov=45)
        json.dumps(c.to_dict())  # should not raise

    def test_to_dict_includes_view_2d(self):
        c = CameraConfig(view_2d=View2DConfig(4.0, 3.0, center=(1.0, 2.0)))
        d = c.to_dict()
        assert d["view_2d"] == {
            "extent_x": 4.0,
            "extent_y": 3.0,
            "center": [1.0, 2.0],
        }

    def test_to_dict_includes_view_plane(self):
        c = CameraConfig(
            view_plane=ViewPlaneConfig(
                point=(0, 0, 0),
                normal=(0, 0, 1),
                extent_u=6.0,
                extent_v=5.0,
            )
        )
        d = c.to_dict()
        assert d["view_plane"]["point"] == [0, 0, 0]
        assert d["view_plane"]["normal"] == [0, 0, 1]
        assert d["view_plane"]["extent_u"] == 6.0
        assert d["view_plane"]["extent_v"] == 5.0
        assert "center" not in d["view_plane"]
        assert "span_u" not in d["view_plane"]


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
        sc = SceneConfig(camera=CameraConfig(fov=30))
        d = sc.to_dict()
        assert d["camera"] == {"fov": 30}

    def test_to_dict_with_empty_camera_omitted(self):
        """Empty CameraConfig (all None) should not add 'camera' key."""
        sc = SceneConfig(camera=CameraConfig())
        d = sc.to_dict()
        assert "camera" not in d

    def test_json_serializable(self):
        sc = SceneConfig(camera=CameraConfig(position=(1, 2, 3)))
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
        assert dirty[0]["kind"] == "Point"
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
        s.update_entity(eid, Point(5, 6, 7))
        dirty, _ = s.flush()
        assert dirty[0]["position"] == [5, 6, 7]

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
        labels = s._serialize_labels()
        assert len(labels) == 1
        assert labels[0]["text"] == "test"


# ── Visualizer Basics ──────────────────────────────────────


class TestVisualizer:
    def test_default_construction(self):
        viz = Visualizer()
        assert viz._port == 8765
        assert viz._host == "localhost"
        assert viz._opns is True

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
        cam = CameraConfig(fov=35)
        viz = Visualizer(camera=cam)
        assert viz._config.camera is cam

    def test_add_entity_returns_id(self):
        viz = Visualizer()
        eid = viz.add(Point(1, 2, 3))
        assert isinstance(eid, str)

    def test_add_with_color_normalizes(self):
        viz = Visualizer()
        viz.add(Point(1, 2, 3), color=(1.0, 0.5, 0.0))
        dirty, _ = viz._scene.flush()
        assert dirty[0]["color"] == "#ff8000"

    def test_add_with_4tuple_extracts_opacity(self):
        viz = Visualizer()
        viz.add(Point(1, 2, 3), color=(1.0, 0.0, 0.0, 0.3))
        dirty, _ = viz._scene.flush()
        assert dirty[0]["color"] == "#ff0000"
        assert dirty[0]["opacity"] == 0.3

    def test_add_with_color_and_explicit_opacity(self):
        viz = Visualizer()
        viz.add(Point(1, 2, 3), color=(1.0, 0.0, 0.0, 0.3), opacity=0.8)
        dirty, _ = viz._scene.flush()
        assert dirty[0]["color"] == "#ff0000"
        assert dirty[0]["opacity"] == 0.8  # explicit wins

    def test_add_with_hex_color_passthrough(self):
        viz = Visualizer()
        viz.add(Point(0, 0, 0), color="#abcdef")
        dirty, _ = viz._scene.flush()
        assert dirty[0]["color"] == "#abcdef"

    def test_add_with_style(self):
        from pytanga.viz._styles import PointStyle

        viz = Visualizer()
        viz.add(Point(0, 0, 0), style=PointStyle(size=0.5, color="#00ff00"))
        dirty, _ = viz._scene.flush()
        assert dirty[0]["style"]["size"] == 0.5
        assert dirty[0]["style"]["color"] == "#00ff00"

    def test_update_with_color(self):
        viz = Visualizer()
        eid = viz.add(Point(0, 0, 0))
        viz._scene.flush()
        viz.update(eid, color="#00ff00")
        dirty, _ = viz._scene.flush()
        assert dirty[0]["color"] == "#00ff00"

    def test_remove_delegates(self):
        viz = Visualizer()
        eid = viz.add(Point(0, 0, 0))
        viz.remove(eid)
        assert viz._scene.entity_count == 1  # until flush
        viz._scene.flush()
        assert viz._scene.entity_count == 0

    def test_clear_delegates(self):
        viz = Visualizer()
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

        assert "Sphere" in viz.default_styles
        assert viz.default_styles[Sphere].wireframe is True
        assert viz.default_styles[Sphere].opacity == 0.4

    def test_set_default_color_via_styles(self):
        viz = Visualizer()
        viz.set_default_color("point", "#00ff00")
        assert viz.default_styles["Point"].color == "#00ff00"

    def test_set_default_color_rgba_sets_opacity_too(self):
        viz = Visualizer()
        viz.set_default_color("point", (1.0, 0.0, 0.0, 0.3))
        assert viz.default_styles["Point"].color == "#ff0000"
        assert viz.default_styles["Point"].opacity == 0.3

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
        assert ls.font_size == 14
        assert ls.color == "#ffffff"
        assert ls.background == "rgba(0, 0, 0, 0.6)"
        assert ls.offset_local is None
        assert ls.offset_2d is None
        assert ls.align is None


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
        g = Grid(range_u=10.0, range_v=6.0)
        d = serialize_entity(g, "g1", kind="Grid")
        assert d["kind"] == "Grid"
        assert d["origin"] == [0.0, 0.0, 0.0]
        assert d["dir_u"] == [1.0, 0.0, 0.0]
        assert d["dir_v"] == [0.0, 1.0, 0.0]
        assert d["range_u"] == 10.0
        assert d["range_v"] == 6.0


class TestAxesExpansion:
    def test_axes_3d_expands_to_three_axes(self):
        a = Axes3D(range_u=4, range_v=5, range_w=6, labels=("X", "Y", "Z"))
        axes = a.expand()
        assert len(axes) == 3
        assert [x.label for x in axes] == ["X", "Y", "Z"]
        assert axes[0].end == (4.0, 0.0, 0.0)
        assert axes[1].end == (0.0, 5.0, 0.0)
        assert axes[2].end == (0.0, 0.0, 6.0)

    def test_axes_2d_expands_to_two_axes(self):
        a = Axes2D(range_u=3, range_v=4, labels=("X", "Y"))
        axes = a.expand()
        assert len(axes) == 2
        assert [x.label for x in axes] == ["X", "Y"]
        assert axes[0].end == (3.0, 0.0, 0.0)
        assert axes[1].end == (0.0, 4.0, 0.0)


# ── Default scene objects ──────────────────────────────────


class TestDefaultSceneObjects:
    def _kinds(self, viz):
        return sorted(o.kind for o in viz._scenes[""]._objects.values())

    def test_default_added_when_none_provided(self):
        viz = Visualizer()
        viz._full_state_for("")
        kinds = self._kinds(viz)
        assert "Axis" in kinds
        assert "Grid" in kinds

    def test_default_not_added_when_axis_provided(self):
        viz = Visualizer()
        viz.add(Axis((0, 0, 0), (1, 0, 0)))
        viz._full_state_for("")
        kinds = self._kinds(viz)
        assert "Axis" in kinds
        assert "Grid" not in kinds

    def test_default_not_added_when_grid_provided(self):
        viz = Visualizer()
        viz.add(Grid())
        viz._full_state_for("")
        kinds = self._kinds(viz)
        assert "Grid" in kinds
        assert "Axis" not in kinds
