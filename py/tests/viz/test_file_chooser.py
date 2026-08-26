# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the FileChooser model + filesystem listing (Phase 1)."""

import asyncio
import json
import threading
import time

import pytest

from pytanga.viz import Visualizer
from pytanga.viz._controls import FileChooser, _serialize_one_control
from pytanga.viz._file_browser import list_directory


def test_list_directory_dirs_first_and_hidden_omitted(tmp_path):
    (tmp_path / "b.txt").write_text("x")
    (tmp_path / "a_dir").mkdir()
    (tmp_path / ".hidden").write_text("x")
    (tmp_path / "a.txt").write_text("x")

    result = list_directory(str(tmp_path))

    assert result["error"] is None
    assert result["path"] == str(tmp_path.resolve())
    names = [e["name"] for e in result["entries"]]
    assert names == ["a_dir", "a.txt", "b.txt"]
    assert result["entries"][0]["is_dir"] is True
    assert result["entries"][0]["path"] == str(tmp_path.resolve() / "a_dir")


def test_list_directory_missing_dir():
    result = list_directory("/nonexistent/definitely/missing")
    assert result["error"] == "missing"
    assert result["entries"] == []


def test_list_directory_root_clamping(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "x.txt").write_text("x")

    result = list_directory(str(outside), root=str(root))

    assert result["path"] == str(root.resolve())
    assert result["error"] is None


def test_file_chooser_serialization():
    fc = FileChooser(
        id="fc", label="File", value="/a/b", placeholder="Path…", root="/a"
    )
    assert _serialize_one_control(fc) == {
        "id": "fc",
        "kind": "file_chooser",
        "label": "File",
        "value": "/a/b",
        "placeholder": "Path…",
        "root": "/a",
        "accept": "",
    }


# ── Phase 2 — Visualizer file-chooser API + dispatch ────────


class _FakeServer:
    def __init__(self) -> None:
        self.pushed: list[str] = []

    async def push_raw(self, data: str) -> None:
        self.pushed.append(data)


def _viz() -> Visualizer:
    return Visualizer(add_default_axes=False, add_default_grid=False)


def _running_loop():
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    return loop, thread


def test_add_file_chooser_registers_and_pushes(monkeypatch):
    viz = _viz()
    pushed: list = []
    monkeypatch.setattr(viz, "_push_controls", lambda scene: pushed.append(scene))

    async def _on_change(path, event):
        pass

    cid = viz.add_file_chooser("fc", value="/tmp", on_change=_on_change)

    assert cid == "fc"
    assert viz._handler_registry.get("fc") is _on_change
    ctrl = viz._scenes[""]._controls["fc"]
    assert isinstance(ctrl, FileChooser)
    assert ctrl.value == "/tmp"
    assert pushed == [""]


def test_open_file_chooser_pushes_show():
    viz = _viz()
    viz._server = _FakeServer()
    viz.add_file_chooser("fc", value="/tmp")
    loop, thread = _running_loop()
    viz._loop = loop
    try:
        viz.open_file_chooser("fc")
        deadline = time.monotonic() + 2
        while not viz._server.pushed and time.monotonic() < deadline:
            time.sleep(0.01)
        assert any('"file_browser_show"' in d for d in viz._server.pushed)
        msg = json.loads(viz._server.pushed[0])
        assert msg["type"] == "file_browser_show"
        assert msg["control_id"] == "fc"
        assert msg["path"] == "/tmp"
    finally:
        loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout=2)


@pytest.mark.anyio
async def test_dispatch_file_browser_select():
    viz = _viz()
    viz._server = _FakeServer()
    calls = []

    async def _on_change(path, event):
        calls.append(path)

    viz.add_file_chooser("fc", on_change=_on_change)
    await viz._dispatch_control_event(
        "file_browser_select", {"control_id": "fc", "path": "/data/x.csv"}
    )

    assert calls == ["/data/x.csv"]
    assert viz._scenes[""]._controls["fc"].value == "/data/x.csv"


@pytest.mark.anyio
async def test_dispatch_file_browser_navigate(tmp_path):
    viz = _viz()
    viz._server = _FakeServer()
    viz.add_file_chooser("fc", root=str(tmp_path))

    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "sub").mkdir()

    await viz._dispatch_control_event(
        "file_browser_navigate",
        {"control_id": "fc", "path": str(tmp_path)},
    )

    assert len(viz._server.pushed) == 1
    msg = json.loads(viz._server.pushed[0])
    assert msg["type"] == "file_browser_listing"
    assert msg["control_id"] == "fc"
    assert [e["name"] for e in msg["entries"]] == ["sub", "a.txt"]
    assert msg["error"] is None


# ── Phase 4 — FileChooserView (layout control view) ─────────


def test_file_chooser_view_serialization():
    from pytanga.viz.views import FileChooserView

    fc = FileChooserView("fc", label="File", value="/tmp", root="/tmp")
    data = fc._serialize(iter(["n0"]))

    assert data["type"] == "file_chooser_view"
    assert data["id"] == "fc"
    assert data["label"] == "File"
    assert data["value"] == "/tmp"
    assert data["root"] == "/tmp"
    assert data["placeholder"] == ""
    assert data["accept"] == ""


def test_set_layout_registers_file_chooser_handler():
    from pytanga.viz.views import FileChooserView

    viz = _viz()

    async def _on_change(path, event):
        pass

    viz.set_layout(FileChooserView("fc", on_change=_on_change))
    assert viz._handler_registry.get("fc") is _on_change
