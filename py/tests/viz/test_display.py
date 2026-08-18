# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for Jupyter display helpers (``display_static`` / ``display_snapshot``)."""

from pytanga.geometry.entities import Point
from pytanga.viz.visualizer import Visualizer


def _viz() -> Visualizer:
    return Visualizer(add_default_axes=False, add_default_grid=False)


class TestDisplayStaticJupyter:
    def test_returns_iframe_with_srcdoc(self):
        viz = _viz()
        viz._jupyter = True
        result = viz.display_static()
        assert hasattr(result, "data")
        assert result.data.startswith("<iframe srcdoc=")

    def test_srcdoc_content_is_escaped(self):
        viz = _viz()
        viz._jupyter = True
        result = viz.display_static()
        data = result.data
        # The standalone document must be HTML-escaped inside the attribute,
        # not injected as raw tags.
        assert "&lt;!DOCTYPE html&gt;" in data
        assert "<html" not in data
        assert "<style" not in data
        assert "<body" not in data

    def test_int_width_height_get_px_suffix(self):
        viz = _viz()
        viz._jupyter = True
        result = viz.display_static(width=400, height=300)
        assert 'width="400px"' in result.data
        assert 'height="300px"' in result.data


class TestDisplayStaticNonJupyter:
    def test_opens_browser_and_returns_none(self, monkeypatch, tmp_path):
        viz = _viz()
        viz._jupyter = False
        opened = []

        def _open(url: str) -> None:
            opened.append(url)

        monkeypatch.setattr("webbrowser.open", _open)
        monkeypatch.setattr(
            "tempfile.mktemp", lambda suffix: str(tmp_path / ("snapshot" + suffix))
        )

        assert viz.display_static() is None
        assert len(opened) == 1
        assert (tmp_path / "snapshot.html").exists()
