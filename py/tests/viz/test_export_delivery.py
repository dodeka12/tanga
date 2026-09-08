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
