# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for standalone & figure HTML export with the scene-graph hierarchy."""

from pathlib import Path

import pytanga.viz
from pytanga.geometry.entities import Point
from pytanga.viz.export._figure_html import render_figure
from pytanga.viz.export._html import render_snapshot
from pytanga.viz.scene import Scene


def _group_scene() -> Scene:
    s = Scene()
    group = s.add_group("grp")
    child_id = s.add(Point(1, 2, 3))
    group.add_child(s.get_node(child_id))
    return s


class TestExportStatic:
    def test_static_full_state_has_parent_and_transform(self):
        s = _group_scene()
        state = s.full_state()
        group = next(d for d in state if d["kind"] == "VizGroup")
        child = next(d for d in state if d["kind"] == "Point")
        assert child["parent_id"] == group["id"]
        assert "transform" in child
        assert "transform" in group

    def test_static_group_kind(self):
        s = _group_scene()
        kinds = {d["kind"] for d in s.full_state()}
        assert "VizGroup" in kinds

    def test_static_render_html(self):
        s = _group_scene()
        html = render_snapshot(s.full_state(), s.config.to_dict())
        assert "function createEntityMesh(" in html
        assert "function createVizGroup(" in html
        assert "function buildSceneObject(" in html
        assert "function buildOverlay(" in html

    def test_figure_html_generation(self):
        s = _group_scene()
        html = render_figure(
            s.full_state(),
            s.config.to_dict(),
            {"width": 400, "height": 300},
            {"title": "T"},
        )
        assert "function createVizGroup(" in html
        assert "function buildSceneObject(" in html

    def test_parent_before_child(self):
        s = _group_scene()
        nodes = s._dfs_preorder()
        ids = [n.id for n in nodes]
        group = next(n for n in nodes if n.kind == "VizGroup")
        child = next(n for n in nodes if n.kind == "Point")
        assert ids.index(group.id) < ids.index(child.id)

    def test_static_render_html_embeds_label_rotation(self, tmp_path):
        viz = pytanga.viz.Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add(
            Point(1, 2, 3),
            label="tilted",
            label_style=pytanga.viz.LabelStyle(rotation=45),
        )
        path = tmp_path / "rotated.html"
        viz.export_snapshot(str(path), overwrite=True)
        content = path.read_text(encoding="utf-8")
        assert '"rotation": 45' in content
        assert "rotate(${rotation}deg)" in content
        assert "transformOrigin" in content

    def test_export_figure_returns_string_when_no_path(self):
        viz = pytanga.viz.Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add(Point(1, 2, 3))
        snippet = viz.export_figure()
        assert isinstance(snippet, str)
        assert "function createEntityMesh(" in snippet

    def test_export_figure_html_alias_deprecated(self):
        import pytest

        viz = pytanga.viz.Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add(Point(1, 2, 3))
        with pytest.warns(DeprecationWarning):
            exporter = pytanga.viz.SceneExporter(viz)
            snippet = exporter.export_figure_html()
        assert isinstance(snippet, str)
        assert "function createEntityMesh(" in snippet


class TestAnimatedExport:
    def test_recording_and_export_snapshot(self, tmp_path):
        viz = pytanga.viz.Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add(Point(1, 2, 3))
        rec = viz.start_animation_recording()
        rec.capture_frame()
        assert rec.frame_count == 1
        path = tmp_path / "anim.html"
        viz.export_snapshot(str(path), animation=rec, overwrite=True)
        content = path.read_text(encoding="utf-8")
        assert "tanga-fig-" in content

    def test_export_figure_animation_returns_string(self):
        viz = pytanga.viz.Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add(Point(1, 2, 3))
        rec = viz.start_animation_recording()
        rec.capture_frame()
        snippet = viz.export_figure(animation=rec)
        assert isinstance(snippet, str)
        assert "tanga-fig-" in snippet

    def test_export_animated_html_alias_deprecated(self, tmp_path):
        import pytest

        viz = pytanga.viz.Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add(Point(1, 2, 3))
        with pytest.warns(DeprecationWarning):
            exporter = pytanga.viz.SceneExporter(viz)
            rec = exporter.start_animation_recording()
            rec.capture_frame()
            path = tmp_path / "anim.html"
            exporter.export_animated_html(str(path), rec, overwrite=True)
        assert path.exists()


    def test_scene_exporter_deprecated(self):
        import pytest

        viz = pytanga.viz.Visualizer(add_default_axes=False, add_default_grid=False)
        with pytest.warns(DeprecationWarning):
            pytanga.viz.SceneExporter(viz)


class TestCdnUnreachableDetection:
    def test_export_cdn_probe_present(self):
        from pytanga.viz.export._bootstrap._errors import js_cdn_check_script

        script = js_cdn_check_script()
        assert "__tanga_cdn_failed" in script
        assert "cdn.jsdelivr.net/npm/three" in script
        assert "AbortError" in script
        # A runtime error must be reported distinctly from a CDN failure.
        assert "RUNTIME_ERROR_MESSAGE" in script
        assert "Viewer error" in script

    def test_live_viewer_cdn_probe_present(self):
        html = (
            Path(pytanga.viz.__file__).parent / "templates" / "viewer.html"
        ).read_text(encoding="utf-8")
        assert "__tanga_cdn_failed" in html
        assert "cdn.jsdelivr.net" in html
        assert "RUNTIME_ERROR_MESSAGE" in html
        assert "Viewer error" in html
