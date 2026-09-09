# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""Tests for the three HTML delivery modes (cdn / inline / offline)."""

import pytest

import pytanga.viz.export._offline as offline
from pytanga.geometry.entities import Point
from pytanga.viz import Visualizer
from pytanga.viz.export._figure_html import render_figure
from pytanga.viz.export._html import render_snapshot
from pytanga.viz.scene import Scene


def _scene() -> Scene:
    s = Scene()
    s.add(Point(1, 2, 3))
    return s


def _toolchain_available() -> bool:
    try:
        offline.find_node()
        offline.find_esbuild()
    except offline.OfflineToolchainError:
        return False
    return True


requires_toolchain = pytest.mark.skipif(
    not _toolchain_available(), reason="node/esbuild unavailable"
)


def test_snapshot_cdn_references_bundle():
    s = _scene()
    html = render_snapshot(s.full_state(), s.config.to_dict())
    assert "cdn.jsdelivr.net/gh/dodeka12/tanga" in html
    assert "function createEntityMesh(" not in html


def test_snapshot_inline_inlines_library():
    s = _scene()
    html = render_snapshot(s.full_state(), s.config.to_dict(), delivery="inline")
    assert "function createEntityMesh(" in html
    assert "cdn.jsdelivr.net/gh/dodeka12/tanga" not in html
    assert '<script type="importmap">' in html


@requires_toolchain
def test_snapshot_offline_inlines_everything():
    s = _scene()
    html = render_snapshot(s.full_state(), s.config.to_dict(), delivery="offline")
    assert "function createEntityMesh(" in html
    assert "cdn.jsdelivr.net/gh/dodeka12/tanga" not in html
    assert '<script type="importmap">' not in html
    assert "html2canvas" in html


def test_figure_cdn_references_bundle():
    s = _scene()
    html = render_figure(
        s.full_state(),
        s.config.to_dict(),
        {"width": 400, "height": 300},
        {},
        delivery="cdn",
    )
    assert "cdn.jsdelivr.net/gh/dodeka12/tanga" in html
    assert "function createEntityMesh(" not in html


def test_snapshot_cdn_references_theme_css():
    s = _scene()
    html = render_snapshot(s.full_state(), s.config.to_dict())
    assert "/py/pytanga/viz/templates/themes/base.css" in html
    # Static exports have no themed controls, so component sheets are dropped.
    assert "controls/button.css" not in html
    assert "--tanga-bg: #1a1a2e" not in html


def test_snapshot_inline_inlines_shell_without_components():
    s = _scene()
    html = render_snapshot(s.full_state(), s.config.to_dict(), delivery="inline")
    assert "--tanga-bg: #1a1a2e" in html
    assert ".tanga-action-button" not in html


def test_snapshot_external_theme_falls_back_to_inline(tmp_path):
    from pytanga.viz._themes import register_theme, registry

    theme_dir = tmp_path / "corp"
    theme_dir.mkdir()
    (theme_dir / "tokens.css").write_text(
        ":root { --tanga-bg: #123456; }\n", encoding="utf-8"
    )
    register_theme("corp_cdn_fallback", theme_dir)
    try:
        s = _scene()
        html = render_snapshot(
            s.full_state(),
            s.config.to_dict(),
            theme="corp_cdn_fallback",
            delivery="cdn",
        )
        assert "--tanga-bg: #123456" in html
        assert "themes/user/corp_cdn_fallback" not in html
    finally:
        registry._external.pop("corp_cdn_fallback", None)


def test_resolve_ref_falls_back_to_main_for_dev(monkeypatch):
    import pytanga.viz.export._cdn as cdn

    monkeypatch.setattr(cdn, "_git_ref", lambda: None)
    monkeypatch.setattr(cdn.importlib.metadata, "version", lambda _: "1.8.1.dev1+gabc")
    assert cdn.resolve_delivery_ref() == "main"


def test_display_snapshot_defaults_to_cdn():
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz.add(Point(1, 2, 3))
    html = viz._render_snapshot_html("")
    assert "cdn.jsdelivr.net/gh/dodeka12/tanga" in html


def test_animated_figure_honours_delivery():
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz.add(Point(1, 2, 3))
    rec = viz.start_animation_recording()
    rec.capture_frame()
    inline = viz.export_figure(animation=rec, delivery="inline")
    assert "function createEntityMesh(" in inline
    cdn = viz.export_figure(animation=rec, delivery="cdn")
    assert "cdn.jsdelivr.net/gh/dodeka12/tanga" in cdn


def test_animated_export_bridge_exposes_entity_mesh_updaters():
    """Regression: the animated adapter calls ``updateEntityMesh``/``removeEntityMesh``.

    Those two functions are imported by the live viewer (``three-view.js``), but the
    exported HTML adapter runs against the ``window.__tanga`` bridge and must
    destructure them from it — otherwise playback throws ``ReferenceError:
    updateEntityMesh is not defined`` on frame 1+.
    """
    from pytanga.viz.export._bootstrap import (
        generate_library_js,
        js_tanga_bridge,
        js_tanga_destructure,
    )

    for source in (js_tanga_destructure(), js_tanga_bridge(), generate_library_js()):
        assert "updateEntityMesh" in source
        assert "removeEntityMesh" in source

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz.add(Point(1, 2, 3))
    rec = viz.start_animation_recording()
    rec.capture_frame()
    html = viz.export_figure(animation=rec, delivery="inline")
    assert "updateEntityMesh" in html
    assert "removeEntityMesh" in html


def test_offline_raises_when_toolchain_missing(monkeypatch):
    offline._build_assets.cache_clear()

    def _raise():
        raise offline.OfflineToolchainError("no esbuild")

    monkeypatch.setattr(offline, "find_esbuild", _raise)
    with pytest.raises(offline.OfflineToolchainError):
        offline.ensure_offline_assets()


@requires_toolchain
def test_end_to_end_writes_all_three_modes(tmp_path):
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz.add(Point(1, 2, 3))
    for delivery in ("cdn", "inline", "offline"):
        path = tmp_path / f"{delivery}.html"
        viz.export_snapshot(str(path), overwrite=True, delivery=delivery)
        content = path.read_text(encoding="utf-8")
        assert "tanga-fig-" in content or "tanga-scene-data" in content
