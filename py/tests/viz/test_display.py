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
    """Idempotent ``display()`` for the live viewer."""

    def _patch_display(self, monkeypatch, captured):
        monkeypatch.setattr(
            "IPython.display.display", lambda obj, **kw: captured.append((obj, kw))
        )

    def test_no_server_prints_hint_and_skips_iframe(self, monkeypatch, capsys):
        viz = _viz()
        viz._jupyter = True
        captured = []
        self._patch_display(monkeypatch, captured)

        result = viz.display()

        assert result is None
        assert captured == []
        assert "start_server()" in capsys.readouterr().out

    def test_emits_iframe_once(self, monkeypatch):
        viz = _viz()
        viz._jupyter = True
        viz._server = object()  # non-None → "running"
        flushes = []
        monkeypatch.setattr(viz, "flush", lambda: flushes.append(True))
        captured = []
        self._patch_display(monkeypatch, captured)

        result = viz.display()

        assert result is None
        assert len(captured) == 1
        _, kwargs = captured[0]
        assert kwargs["display_id"] == "tanga-main"
        assert flushes == [True]

    def test_repeat_display_flushes_without_emitting(self, monkeypatch):
        viz = _viz()
        viz._jupyter = True
        viz._server = object()
        flushes = []
        monkeypatch.setattr(viz, "flush", lambda: flushes.append(True))
        captured = []
        self._patch_display(monkeypatch, captured)

        viz.display()
        viz.display()

        assert len(captured) == 1
        assert flushes == [True, True]

    def test_new_execution_emits_again(self, monkeypatch):
        viz = _viz()
        viz._jupyter = True
        viz._server = object()
        monkeypatch.setattr(viz, "flush", lambda: None)
        captured = []
        self._patch_display(monkeypatch, captured)

        import pytanga.viz.visualizer as vizmod

        tokens = iter([1, 1, 2])
        monkeypatch.setattr(vizmod, "execution_token", lambda: next(tokens))

        viz.display()  # token 1 → new execution → emit
        viz.display()  # token 1 → same execution → no emit
        viz.display()  # token 2 → new execution → emit

        assert len(captured) == 2

    def test_caller_viewer_name_is_used(self, monkeypatch):
        viz = _viz()
        viz._jupyter = True
        viz._server = object()
        captured = []
        self._patch_display(monkeypatch, captured)

        viz.display(viewer_name="cell-a")

        assert len(captured) == 1
        iframe, kwargs = captured[0]
        assert kwargs["display_id"] == "tanga-cell-a"
        assert iframe.src.endswith("?viewer=cell-a")

    def test_scene_handle_emits_for_its_scene(self, monkeypatch):
        viz = _viz()
        viz._jupyter = True
        viz._server = object()
        monkeypatch.setattr(viz, "flush", lambda: None)
        handle = viz.scene("detail")
        captured = []
        self._patch_display(monkeypatch, captured)

        result = handle.display()

        assert result is None
        assert len(captured) == 1
        iframe, kwargs = captured[0]
        assert kwargs["display_id"] == "tanga-detail"
        assert iframe.src.endswith("?viewer=detail")


class TestContextManager:
    def test_with_viz_shows_on_entry_and_flushes_on_exit(self, monkeypatch):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        calls = []
        monkeypatch.setattr(
            viz, "_reset_scene", lambda name: calls.append(("reset", name))
        )
        monkeypatch.setattr(viz, "show", lambda: calls.append(("show",)))
        monkeypatch.setattr(viz, "flush", lambda **kw: calls.append(("flush",)))

        with viz as v:
            assert v is viz
            # show() happens on entry, before the body runs
            assert calls == [("reset", ""), ("show",)]

        assert calls == [("reset", ""), ("show",), ("flush",)]

    def test_with_scene_shows_on_entry_and_flushes_on_exit(self, monkeypatch):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        handle = viz.scene("detail")
        calls = []
        monkeypatch.setattr(
            viz, "_reset_scene", lambda name: calls.append(("reset", name))
        )
        monkeypatch.setattr(handle, "show", lambda: calls.append(("show",)))
        monkeypatch.setattr(handle, "flush", lambda **kw: calls.append(("flush",)))

        with handle as h:
            assert h is handle
            assert calls == [("reset", "detail"), ("show",)]

        assert calls == [("reset", "detail"), ("show",), ("flush",)]

    def test_exit_propagates_exception(self, monkeypatch):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        monkeypatch.setattr(viz, "_reset_scene", lambda name: None)
        monkeypatch.setattr(viz, "show", lambda: None)
        monkeypatch.setattr(viz, "flush", lambda **kw: None)

        with pytest.raises(RuntimeError):
            with viz:
                raise RuntimeError("boom")

    def test_with_viz_preserves_default_axes_grid(self, monkeypatch):
        viz = Visualizer()  # defaults: axes + grid enabled
        monkeypatch.setattr(viz, "show", lambda: None)
        monkeypatch.setattr(viz, "flush", lambda **kw: None)

        def kinds():
            return sorted(o.kind for o in viz._scenes[""]._objects.values())

        assert "Axes3D" in kinds()
        assert "Grid" in kinds()

        with viz:
            pass

        assert "Axes3D" in kinds()
        assert "Grid" in kinds()
