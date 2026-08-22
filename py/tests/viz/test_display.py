# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for Jupyter display helpers (``display_snapshot`` / ``display_static``)."""

import pytest

from pytanga.viz.visualizer import Visualizer


def _viz() -> Visualizer:
    return Visualizer(add_default_axes=False, add_default_grid=False)


class TestDisplaySnapshotJupyter:
    def test_returns_iframe_with_data_url(self):
        viz = _viz()
        viz._jupyter = True
        result = viz.display_snapshot()
        assert result.src.startswith("data:text/html;charset=utf-8;base64,")
        assert "<iframe" in result._repr_html_()

    def test_src_is_base64_not_raw_html(self):
        viz = _viz()
        viz._jupyter = True
        result = viz.display_snapshot()
        # The standalone document must be embedded as base64 in a data URL,
        # never injected as raw tags.
        assert "<html" not in result.src
        assert "<style" not in result.src
        assert "<body" not in result.src

    def test_int_width_height_get_px_suffix(self):
        viz = _viz()
        viz._jupyter = True
        result = viz.display_snapshot(width=400, height=300)
        assert result.width == "400px"
        assert result.height == "300px"

    def test_display_static_alias(self):
        viz = _viz()
        viz._jupyter = True
        with pytest.warns(DeprecationWarning):
            result = viz.display_static()
        assert result.src.startswith("data:text/html;charset=utf-8;base64,")


class TestDisplaySnapshotNonJupyter:
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

        assert viz.display_snapshot() is None
        assert len(opened) == 1
        assert (tmp_path / "snapshot.html").exists()


class TestDisplayRow:
    def _handles(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        return viz, viz.scene("one"), viz.scene("two")

    def test_display_live_main_scene_non_jupyter(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz._jupyter = False
        html = viz.display()
        assert "<iframe src=" in html
        assert viz.url in html

    def test_display_row_live(self, monkeypatch):
        viz, one, two = self._handles()
        captured = []
        monkeypatch.setattr("IPython.display.display", lambda obj: captured.append(obj))
        viz.display_row((one, None), (two, None))
        assert len(captured) == 1
        assert captured[0].data.count("<iframe src=") == 2

    def test_display_row_static(self, monkeypatch):
        viz, one, two = self._handles()
        captured = []
        monkeypatch.setattr("IPython.display.display", lambda obj: captured.append(obj))
        viz.display_row((one, None), (two, None), mode="static")
        assert len(captured) == 1
        assert captured[0].data.count("data:text/html;charset=utf-8;base64,") == 2
        assert "<html" not in captured[0].data


class TestDisplayLiveJupyter:
    """``display()`` must hint instead of rendering an empty iframe when the
    server has not been started."""

    def test_no_server_prints_hint_and_skips_iframe(self, monkeypatch, capsys):
        viz = _viz()
        viz._jupyter = True
        displayed = []
        monkeypatch.setattr("IPython.display.display", lambda obj: displayed.append(obj))

        result = viz.display()

        assert result is None
        assert displayed == []
        assert "start_server()" in capsys.readouterr().out

    def test_server_running_displays_iframe(self, monkeypatch):
        viz = _viz()
        viz._jupyter = True
        viz._server = object()  # non-None → treated as running
        displayed = []
        monkeypatch.setattr("IPython.display.display", lambda obj: displayed.append(obj))

        result = viz.display()

        assert result is None
        assert len(displayed) == 1
        assert displayed[0].src == viz.url

    def test_scene_handle_no_server_prints_hint(self, monkeypatch, capsys):
        viz = _viz()
        viz._jupyter = True
        handle = viz.scene("detail")
        displayed = []
        monkeypatch.setattr("IPython.display.display", lambda obj: displayed.append(obj))

        result = handle.display()

        assert result is None
        assert displayed == []
        assert "start_server()" in capsys.readouterr().out

    def test_scene_handle_server_running_displays_iframe(self, monkeypatch):
        viz = _viz()
        viz._jupyter = True
        viz._server = object()
        handle = viz.scene("detail")
        displayed = []
        monkeypatch.setattr("IPython.display.display", lambda obj: displayed.append(obj))

        result = handle.display()

        assert result is None
        assert len(displayed) == 1
        assert displayed[0].src == handle.url

