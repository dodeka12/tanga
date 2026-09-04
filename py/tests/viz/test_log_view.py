# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the `LogView` data model (`views.py`)."""

from __future__ import annotations

import asyncio
import json

import pytest

from pytanga.viz import Visualizer
from pytanga.viz.views import LogView, serialize_layout


class _FakeServer:
    def __init__(self):
        self.pushed: list[str] = []

    async def push_raw(self, data: str) -> None:
        self.pushed.append(data)


def _patch_push(viz: Visualizer, server: _FakeServer, monkeypatch) -> None:
    monkeypatch.setattr(viz, "_server", server)
    monkeypatch.setattr(viz, "_loop", object())
    monkeypatch.setattr(
        asyncio, "run_coroutine_threadsafe", lambda coro, loop: asyncio.run(coro)
    )


def _messages(server: _FakeServer) -> list[dict]:
    return [json.loads(d) for d in server.pushed]


def _push_calls(view: LogView) -> list[tuple]:
    calls: list[tuple] = []
    view._push = lambda vid, action, lines=None: calls.append((vid, action, lines))
    return calls


def test_log_str_line() -> None:
    view = LogView()
    view.log("x")
    line = view.lines[0]
    assert set(line) == {"time", "message"}
    assert line["message"] == "x"
    assert line["time"].endswith("+00:00")  # UTC ISO-8601


def test_log_dict_folds_keys() -> None:
    view = LogView()
    view.log({"message": "hi", "level": "info"})
    line = view.lines[0]
    assert line["message"] == "hi"
    assert line["level"] == "info"
    assert "time" in line


def test_max_history_drops_oldest() -> None:
    view = LogView(max_history=2)
    view.log("a")
    view.log("b")
    view.log("c")
    assert [l["message"] for l in view.lines] == ["b", "c"]


def test_max_history_none_keeps_all() -> None:
    view = LogView()
    for msg in ("a", "b", "c"):
        view.log(msg)
    assert len(view.lines) == 3


def test_get_log_returns_copies() -> None:
    view = LogView()
    view.log("a")
    lines = view.get_log()
    lines[0]["message"] = "mutated"
    assert view.lines[0]["message"] == "a"


def test_clear_empties() -> None:
    view = LogView()
    view.log("a")
    view.clear()
    assert view.lines == []


def test_write_load_round_trip(tmp_path) -> None:
    view = LogView()
    view.log("a")
    view.log({"message": "b", "level": "warn"})
    path = tmp_path / "log.jsonl"
    view.write_file(path)
    raw = path.read_text(encoding="utf-8").splitlines()
    assert len(raw) == 2
    assert json.loads(raw[0])["message"] == "a"

    other = LogView()
    other.load_file(path)
    assert other.get_log() == view.get_log()


def test_load_file_truncates_to_max_history(tmp_path) -> None:
    path = tmp_path / "log.jsonl"
    path.write_text(
        '{"time": "t", "message": "a"}\n'
        '{"time": "t", "message": "b"}\n'
        '{"time": "t", "message": "c"}\n',
        encoding="utf-8",
    )
    view = LogView(max_history=2)
    view.load_file(path)
    assert [l["message"] for l in view.lines] == ["b", "c"]


def test_serialize() -> None:
    view = LogView(id="log0", max_history=1000)
    view.log("x")
    node = serialize_layout(view)["root"]
    assert node["type"] == "log_view"
    assert node["id"] == "log0"
    assert node["max_history"] == 1000
    assert node["lines"][0]["message"] == "x"


def test_auto_id_assigned() -> None:
    a = LogView()
    b = LogView()
    assert a.id.startswith("log")
    assert b.id.startswith("log")
    assert a.id != b.id


def test_log_push_callback() -> None:
    view = LogView(id="log0")
    calls = _push_calls(view)
    view.log("x")
    assert calls == [("log0", "append", [{"time": view.lines[0]["time"], "message": "x"}])]


def test_clear_push_callback() -> None:
    view = LogView(id="log0")
    calls = _push_calls(view)
    view.clear()
    assert calls == [("log0", "clear", None)]


def test_load_file_push_callback(tmp_path) -> None:
    path = tmp_path / "log.jsonl"
    path.write_text('{"time": "t", "message": "a"}\n', encoding="utf-8")
    view = LogView(id="log0")
    calls = _push_calls(view)
    view.load_file(path)
    assert calls[0][0] == "log0"
    assert calls[0][1] == "replace"
    assert calls[0][2] == [{"time": "t", "message": "a"}]


def test_log_no_push_noop() -> None:
    view = LogView()
    view.log("x")  # _push is None; must not raise
    assert view.lines[0]["message"] == "x"


def test_invalid_max_history_raises() -> None:
    with pytest.raises(ValueError):
        LogView(max_history=-1)
    with pytest.raises(ValueError):
        LogView(max_history="nope")


# ── Live updates (log_update push) ───────────────────────────


def test_set_layout_injects_push_and_log_pushes_log_update(monkeypatch) -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    log_view = LogView(id="log0")
    viz.set_layout(log_view)
    server = _FakeServer()
    _patch_push(viz, server, monkeypatch)

    log_view.log("hello")

    log_msgs = [m for m in _messages(server) if m.get("type") == "log_update"]
    assert len(log_msgs) == 1
    msg = log_msgs[0]
    assert msg["id"] == "log0"
    assert msg["action"] == "append"
    assert msg["lines"][0]["message"] == "hello"
    assert "time" in msg["lines"][0]


def test_clear_pushes_log_update(monkeypatch) -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    log_view = LogView(id="log0")
    viz.set_layout(log_view)
    server = _FakeServer()
    _patch_push(viz, server, monkeypatch)

    log_view.clear()

    log_msgs = [m for m in _messages(server) if m.get("type") == "log_update"]
    assert log_msgs == [{"type": "log_update", "id": "log0", "action": "clear"}]


def test_load_file_pushes_replace(monkeypatch, tmp_path) -> None:
    path = tmp_path / "log.jsonl"
    path.write_text('{"time": "t", "message": "a"}\n', encoding="utf-8")

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    log_view = LogView(id="log0")
    viz.set_layout(log_view)
    server = _FakeServer()
    _patch_push(viz, server, monkeypatch)

    log_view.load_file(path)

    log_msgs = [m for m in _messages(server) if m.get("type") == "log_update"]
    assert len(log_msgs) == 1
    assert log_msgs[0]["action"] == "replace"
    assert log_msgs[0]["lines"] == [{"time": "t", "message": "a"}]
