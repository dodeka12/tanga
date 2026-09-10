# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the Jupyter-scoped Visualizer singleton and re-run reset."""

import pytest
from pytanga.geometry import Point

from pytanga.viz import visualizer as viz_module
from pytanga.viz.visualizer import Visualizer


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Clear the Jupyter-scoped singleton before and after each test."""
    Visualizer.reset()
    yield
    Visualizer.reset()


def _set_jupyter(monkeypatch, value: bool) -> None:
    monkeypatch.setattr(viz_module, "_is_jupyter", lambda: value)


class TestSingleton:
    def test_same_instance_under_jupyter(self, monkeypatch):
        _set_jupyter(monkeypatch, True)
        assert Visualizer() is Visualizer()

    def test_distinct_instances_outside_jupyter(self, monkeypatch):
        _set_jupyter(monkeypatch, False)
        assert Visualizer() is not Visualizer()

    def test_reset_yields_fresh_instance(self, monkeypatch):
        _set_jupyter(monkeypatch, True)
        first = Visualizer()
        Visualizer.reset()
        second = Visualizer()
        assert first is not second


class TestConstructorRerunReset:
    def test_rerun_clears_and_readds_axes_grid(self, monkeypatch):
        _set_jupyter(monkeypatch, True)
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        eid = viz.add(Point(1, 2, 3))
        scene = viz._scenes[""]
        assert eid in scene._objects

        viz2 = Visualizer(add_default_axes=True, add_default_grid=True)
        assert viz2 is viz
        scene.flush()  # apply the pending removal from the reset
        assert eid not in scene._objects
        kinds = {o.kind for o in scene._objects.values()}
        assert "Axes3D" in kinds
        assert "Grid" in kinds

    def test_rerun_without_axes_grid_readds_nothing(self, monkeypatch):
        _set_jupyter(monkeypatch, True)
        viz = Visualizer(add_default_axes=True, add_default_grid=True)
        viz.add(Point(1, 2, 3))
        scene = viz._scenes[""]

        viz2 = Visualizer(add_default_axes=False, add_default_grid=False)
        assert viz2 is viz
        scene.flush()
        assert scene._objects == {}


class TestSceneRerunClear:
    def test_scene_rerun_clears_same_cell(self, monkeypatch):
        _set_jupyter(monkeypatch, True)
        monkeypatch.setattr(viz_module, "current_cell_id", lambda: "cell-a")
        token = {"t": 0}
        monkeypatch.setattr(viz_module, "execution_token", lambda: token["t"])

        viz = Visualizer()
        eid = viz.scene("foo").add(Point(1, 2, 3))
        scene = viz._scenes["foo"]
        assert eid in scene._objects

        # same cell + same token → get-or-create, no clear
        viz.scene("foo")
        assert eid in scene._objects

        # same cell + bumped token → re-run: clear + re-add defaults
        token["t"] = 1
        viz.scene("foo")
        scene.flush()
        assert eid not in scene._objects

    def test_scene_different_cell_does_not_clear(self, monkeypatch):
        _set_jupyter(monkeypatch, True)
        monkeypatch.setattr(viz_module, "current_cell_id", lambda: "cell-a")
        token = {"t": 0}
        monkeypatch.setattr(viz_module, "execution_token", lambda: token["t"])

        viz = Visualizer()
        eid = viz.scene("foo").add(Point(1, 2, 3))
        scene = viz._scenes["foo"]

        monkeypatch.setattr(viz_module, "current_cell_id", lambda: "cell-b")
        token["t"] = 1
        viz.scene("foo")
        scene.flush()
        assert eid in scene._objects


class TestConfigScope:
    def test_non_jupyter_distinct_configs(self, monkeypatch):
        _set_jupyter(monkeypatch, False)
        a = Visualizer(title="A", space_dim=2)
        b = Visualizer(title="B", space_dim=3)
        assert a is not b
        assert a._title == "A"
        assert b._title == "B"
        assert a._scenes[""].config.space_dim == 2
        assert b._scenes[""].config.space_dim == 3

    def test_rerun_first_call_wins_for_non_axes_config(self, monkeypatch):
        _set_jupyter(monkeypatch, True)
        viz = Visualizer(title="First", add_default_axes=False, add_default_grid=False)
        viz2 = Visualizer(title="Second", add_default_axes=True, add_default_grid=True)
        assert viz2 is viz
        assert viz._title == "First"  # non-axes config is first-call-wins
        assert viz._add_default_axes is True  # axes/grid flags were re-applied
        assert viz._add_default_grid is True
