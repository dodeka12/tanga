# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the SDF viewer facade (Phase 6)."""

from __future__ import annotations

from pytanga.geometry.entities import Point, Sphere
from pytanga.viz.sdf.distance import DistanceFunction
from pytanga.viz.sdf.visualizer import SdfVisualizer


def test_add_serializes_sdf_object() -> None:
    viz = SdfVisualizer(open_browser=False)
    oid = viz.add(Sphere(Point(0, 0, 0), 1.0), color="#ff0000")
    assert isinstance(oid, str)
    full_state, _ = viz._full_state_for("")
    assert len(full_state) == 1
    obj = full_state[0]
    assert obj["kind"] == "sdf"
    assert obj["sdfKind"] == "Sphere"
    assert obj["tree"]["kind"] == "sphere"
    assert obj["color"] == "#ff0000"


def test_distance_setter_emits_config_value() -> None:
    viz = SdfVisualizer(open_browser=False)
    assert viz.distance == "scalar_pseudo"
    viz.distance = DistanceFunction.MAGNITUDE
    assert viz.distance == "magnitude"
    viz.opacity = "sigmoid"
    assert viz.opacity == "sigmoid"


def test_camera_config_parity() -> None:
    from pytanga.viz.camera import CameraConfig3d

    cam = CameraConfig3d(position=(10, 6, 12), target=(0, 0, 0), fov=50)

    from pytanga.viz.visualizer import Visualizer

    std_viz = Visualizer(camera=cam, add_default_axes=False, add_default_grid=False)
    sdf_viz = SdfVisualizer(camera=cam, open_browser=False)

    std_cfg = std_viz._scene_config_for("")
    sdf_cfg = sdf_viz._scene_config_for("")

    # The camera dicts must match exactly (camera parity).
    assert std_cfg["camera"] == sdf_cfg["camera"]


def test_default_camera_is_none() -> None:
    viz = SdfVisualizer(open_browser=False)
    cfg = viz._scene_config_for("")
    assert "camera" not in cfg  # none specified → auto-fit on the frontend
    assert cfg["space_dim"] == 3


def test_default_light_added_by_default() -> None:
    viz = SdfVisualizer(open_browser=False)
    lights = viz._lighting_dict()["lights"]
    assert len(lights) == 1
    assert lights[0]["kind"] == "directional"
    # The default light reproduces the historical hardcoded look.
    assert lights[0]["intensity"] == 0.8
    assert viz.ambient == {"color": "#ffffff", "intensity": 0.45}


def test_add_default_light_false() -> None:
    viz = SdfVisualizer(open_browser=False, add_default_light=False)
    assert viz._lighting_dict()["lights"] == []


def test_add_light() -> None:
    from pytanga.viz.sdf.lights import DirectionalLight

    viz = SdfVisualizer(open_browser=False, add_default_light=False)
    lid = viz.add(DirectionalLight(direction=(1, 0, 0), color="#00ff00", intensity=1.0))
    assert lid.startswith("light-")
    lights = viz._lighting_dict()["lights"]
    assert len(lights) == 1
    assert lights[0]["color"] == "#00ff00"
    assert lights[0]["direction"] == [1.0, 0.0, 0.0]


def test_set_ambient_light() -> None:
    viz = SdfVisualizer(open_browser=False)
    assert viz.ambient == {"color": "#ffffff", "intensity": 0.45}
    viz.set_ambient_light(color="#112233", intensity=0.7)
    assert viz.ambient == {"color": "#112233", "intensity": 0.7}


def test_remove_and_clear_lights() -> None:
    from pytanga.viz.sdf.lights import DirectionalLight

    viz = SdfVisualizer(open_browser=False)
    lid = viz.add(DirectionalLight(direction=(0, 0, 1)))
    viz.remove(lid)
    # The built-in default light is untouched by removing the added light.
    assert [light["kind"] for light in viz._lighting_dict()["lights"]] == ["directional"]
    viz.remove("__default_light__")
    assert viz._lighting_dict()["lights"] == []
    viz.add(DirectionalLight())
    viz.clear()
    assert viz._lighting_dict()["lights"] == []


def test_scene_config_carries_lighting() -> None:
    viz = SdfVisualizer(open_browser=False)
    cfg = viz._scene_config_for("")
    assert "sdf_lighting" in cfg
    assert cfg["sdf_lighting"]["ambient"]["intensity"] == 0.45
    assert len(cfg["sdf_lighting"]["lights"]) == 1


def test_update_entity_replaces_object() -> None:
    viz = SdfVisualizer(open_browser=False)
    oid = viz.add(Sphere(Point(0, 0, 0), 1.0), color="#ff0000")
    viz.update_entity(oid, Sphere(Point(1, 0, 0), 2.0), color="#00ff00")
    obj = viz._full_state_for("")[0][0]
    assert obj["id"] == oid
    assert obj["color"] == "#00ff00"
    assert obj["tree"]["params"]["radius"] == 2.0


def test_update_light_replaces_by_id() -> None:
    from pytanga.viz.sdf.lights import DirectionalLight

    viz = SdfVisualizer(open_browser=False, add_default_light=False)
    lid = viz.add(DirectionalLight(direction=(1, 0, 0), color="#ff0000"))
    viz.update_light(lid, DirectionalLight(direction=(0, 1, 0), color="#00ff00"))
    lights = viz._lighting_dict()["lights"]
    assert len(lights) == 1
    assert lights[0]["color"] == "#00ff00"
    assert lights[0]["direction"] == [0.0, 1.0, 0.0]


def test_update_entity_routes_light() -> None:
    from pytanga.viz.sdf.lights import DirectionalLight

    viz = SdfVisualizer(open_browser=False, add_default_light=False)
    lid = viz.add(DirectionalLight(direction=(1, 0, 0)))
    viz.update_entity(lid, DirectionalLight(direction=(0, 0, 1)))
    assert viz._lighting_dict()["lights"][0]["direction"] == [0.0, 0.0, 1.0]


def test_flush_and_sleep_ms() -> None:
    import time

    viz = SdfVisualizer(open_browser=False)
    viz.flush()  # no-op before the server starts
    start = time.monotonic()
    assert viz.sleep_ms(40) is True
    assert time.monotonic() - start >= 0.03


def test_reuse_existing_flag_and_open_browser_guard() -> None:
    import pytest

    assert SdfVisualizer(open_browser=False)._reuse_existing is True
    assert SdfVisualizer(open_browser=False, reuse_existing=False)._reuse_existing is False
    with pytest.raises(RuntimeError):
        SdfVisualizer(open_browser=False).open_browser()