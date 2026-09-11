# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for server lifecycle (loop/handler restore, port-in-use, dead params, layout URL)."""

import asyncio
import errno
import os
import signal
import socket
import subprocess
import sys
import threading

import pytest

from pytanga.viz import Visualizer, VisualizerApp, visualizer as viz_module
from pytanga.viz.server import (
    PortConflictMode,
    PortInUseError,
    VizServer,
    _is_port_in_use_error,
    find_port_occupants,
)


def _viz() -> Visualizer:
    return Visualizer(add_default_axes=False, add_default_grid=False)


# ── 6.1 — start_server must not touch the caller's event loop ──────────────


def test_start_server_does_not_call_set_event_loop(monkeypatch):
    viz = _viz()
    calls: list = []
    monkeypatch.setattr(asyncio, "set_event_loop", lambda loop: calls.append(loop))
    viz.start_server(port=0)
    try:
        assert calls == []
    finally:
        viz.stop_server()


# ── 6.2 — signal handlers are restored on stop ─────────────────────────────


def test_start_stop_restores_signal_handlers():
    viz = _viz()
    before_int = signal.getsignal(signal.SIGINT)
    before_term = signal.getsignal(signal.SIGTERM)
    viz.start_server(port=0)
    viz.stop_server()
    assert signal.getsignal(signal.SIGINT) is before_int
    assert signal.getsignal(signal.SIGTERM) is before_term


# ── 6.3 — a busy port reports a clear message (SystemExit, no traceback) ───


def test_start_server_busy_port_reports_clear_message():
    viz = _viz()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    port = sock.getsockname()[1]
    try:
        with pytest.raises(SystemExit) as excinfo:
            viz.start_server(port=port)
        assert "already in use" in str(excinfo.value)
    finally:
        sock.close()
    assert viz._server is None
    assert viz._loop is None
    assert viz._thread is None


def test_is_port_in_use_error_detects_posix_and_windows():
    # POSIX: EADDRINUSE (98 on Linux, 48 on macOS) with the standard message.
    assert _is_port_in_use_error(OSError(errno.EADDRINUSE, "Address already in use"))
    # Windows: the WinSock error code (10048) with its own message.
    assert _is_port_in_use_error(
        OSError(10048, "only one usage of each socket address is normally permitted")
    )
    # Windows: the error wrapped by asyncio's create_server keeps errno=10048
    # and a mixed message containing the WinSock wording.
    assert _is_port_in_use_error(
        OSError(
            10048,
            "error while attempting to bind on address ('127.0.0.1', 50621): "
            "[winerror 10048] only one usage of each socket address "
            "(protocol/network address/port) is normally permitted",
        )
    )
    # An unrelated OSError is not treated as a busy port.
    assert not _is_port_in_use_error(OSError(errno.ECONNREFUSED, "Connection refused"))


# ── 6.4 — _ensure_server_running surfaces the real boot error ──────────────


def test_ensure_server_running_reraises_boot_error(monkeypatch):
    viz = _viz()

    async def _fail(*args, **kwargs):
        raise PortInUseError("Port 12345 is already in use. Close the other process.")

    monkeypatch.setattr(VizServer, "start", _fail)
    with pytest.raises(PortInUseError):
        viz._ensure_server_running()
    assert viz._server is None
    assert viz._loop is None
    assert viz._thread is None


# ── 6.5 — stop_server restores handlers even when the server is None ───────


def test_stop_server_restores_handlers_when_server_none():
    viz = _viz()
    orig_int = signal.getsignal(signal.SIGINT)
    orig_term = signal.getsignal(signal.SIGTERM)

    def _fake(signum, frame):
        pass

    viz._saved_signal_handlers = {
        signal.SIGINT: orig_int,
        signal.SIGTERM: orig_term,
    }
    signal.signal(signal.SIGINT, _fake)
    signal.signal(signal.SIGTERM, _fake)
    try:
        viz.stop_server()  # _server is None → early return, but restores handlers
        assert signal.getsignal(signal.SIGINT) is orig_int
        assert signal.getsignal(signal.SIGTERM) is orig_term
    finally:
        signal.signal(signal.SIGINT, orig_int)
        signal.signal(signal.SIGTERM, orig_term)


# ── 6.6/6.7 — removed constructor params are rejected ──────────────────────


def test_constructor_rejects_port_host_open_browser():
    with pytest.raises(TypeError):
        Visualizer(port=9000)
    with pytest.raises(TypeError):
        Visualizer(host="127.0.0.1")
    with pytest.raises(TypeError):
        Visualizer(open_browser=False)


# ── 6.8 — VisualizerApp forwards add_default_axes/add_default_grid ──────────


def test_visualizerapp_forwards_add_default_axes_grid():
    app = VisualizerApp(add_default_axes=False, add_default_grid=False)
    assert app.viz._add_default_axes is False
    assert app.viz._add_default_grid is False


# ── 6.9 — VisualizerApp.run threads timeout into show() ────────────────────


def test_visualizerapp_run_threads_timeout(monkeypatch):
    app = VisualizerApp()
    app._stop_requested.set()
    calls: dict = {}
    monkeypatch.setattr(app.viz, "show", lambda **kw: calls.update(kw) or True)
    monkeypatch.setattr(app.viz, "stop_server", lambda **kw: None)
    app.run(wait_for_browser=False, timeout=7.5)
    assert calls["timeout"] == 7.5


def test_visualizerapp_run_forwards_port_host(monkeypatch):
    app = VisualizerApp()
    app._stop_requested.set()
    calls: dict = {}
    monkeypatch.setattr(app.viz, "show", lambda **kw: calls.update(kw) or True)
    monkeypatch.setattr(app.viz, "stop_server", lambda **kw: None)
    app.run(wait_for_browser=False, port=9000, host="127.0.0.1")
    assert calls["port"] == 9000
    assert calls["host"] == "127.0.0.1"


# ── 6.10 — the layout URL is passed through and opened ─────────────────────


def test_open_browser_url_passes_path_to_wait_for_browser(monkeypatch):
    viz = _viz()
    calls: dict = {}
    monkeypatch.setattr(
        viz, "wait_for_browser", lambda **kw: calls.update(kw) or True
    )
    viz._open_browser_url("/?view=main&token=abc", wait_for_browser=True)
    assert calls["path"] == "/?view=main&token=abc"


def test_wait_for_browser_opens_given_path(monkeypatch):
    viz = _viz()
    opened: list = []

    class _FakeLoop:
        def call_soon_threadsafe(self, fn, *args):
            pass

    class _FakeServer:
        def __init__(self):
            self._any_ws_ready_thread = threading.Event()

        def _clear_ws_ready_events(self):
            pass

        def open_browser(self, url):
            opened.append(url)

    viz._server = _FakeServer()
    viz._loop = _FakeLoop()
    monkeypatch.setattr("builtins.input", lambda: "")
    monkeypatch.setattr(viz, "_print_connect_prompt", lambda **kw: None)

    viz.wait_for_browser(timeout=0.0, path="/?view=main&token=abc")
    assert opened == ["/?view=main&token=abc"]


# ── Port-conflict resolution ────────────────────────────────────────────


def _block_port() -> tuple[socket.socket, int]:
    """Bind + listen a socket on 127.0.0.1 and return ``(sock, port)``."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    return sock, sock.getsockname()[1]


def test_find_port_occupants_detects_local_listener():
    sock, port = _block_port()
    try:
        occupants = find_port_occupants(port)
        assert any(o.pid == os.getpid() for o in occupants)
        assert all(o.name for o in occupants)
    finally:
        sock.close()


def test_auto_mode_picks_free_port():
    sock, port = _block_port()
    viz = Visualizer(
        add_default_axes=False,
        add_default_grid=False,
        port_conflict_mode=PortConflictMode.AUTO,
    )
    try:
        viz.start_server(port=port)
        assert viz._port != port
        assert viz._port == viz._server.port
    finally:
        viz.stop_server()
        sock.close()


def test_cancel_mode_reports_busy_port():
    sock, port = _block_port()
    viz = Visualizer(
        add_default_axes=False,
        add_default_grid=False,
        port_conflict_mode=PortConflictMode.CANCEL,
    )
    try:
        with pytest.raises(SystemExit):
            viz.start_server(port=port)
    finally:
        sock.close()


def test_kill_mode_terminates_blocking_process():
    code = (
        "import socket, time; "
        "s = socket.socket(); s.bind(('127.0.0.1', 0)); s.listen(1); "
        "print(s.getsockname()[1], flush=True); time.sleep(60)"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", code], stdout=subprocess.PIPE, text=True
    )
    port = int(proc.stdout.readline().strip())
    viz = Visualizer(
        add_default_axes=False,
        add_default_grid=False,
        port_conflict_mode=PortConflictMode.KILL,
    )
    try:
        viz.start_server(port=port)
        assert proc.wait(timeout=10) is not None  # the blocker was terminated
        assert viz._port == port
    finally:
        viz.stop_server()
        if proc.poll() is None:
            proc.kill()
            proc.wait()


def test_ask_mode_without_handler_cancels():
    sock, port = _block_port()
    server = VizServer(
        host="localhost", port=port, port_conflict_mode=PortConflictMode.ASK
    )

    async def _go() -> None:
        try:
            await server.start(lambda: {}, lambda: {})
        finally:
            await server.stop()

    try:
        with pytest.raises(PortInUseError):
            asyncio.run(_go())
    finally:
        sock.close()


def test_ask_mode_honours_injected_handler():
    sock, port = _block_port()
    viz = Visualizer(
        add_default_axes=False,
        add_default_grid=False,
        port_conflict_mode=PortConflictMode.ASK,
    )
    try:
        viz.start_server(port=port, ask=lambda p, occ: PortConflictMode.AUTO)
        assert viz._port != port
        assert viz._port == viz._server.port
    finally:
        viz.stop_server()
        sock.close()


def test_visualizer_default_mode_resolution(monkeypatch):
    Visualizer.reset()
    try:
        monkeypatch.setattr(viz_module, "_is_jupyter", lambda: True)
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        assert viz._port_conflict_mode is PortConflictMode.AUTO

        Visualizer.reset()
        monkeypatch.setattr(viz_module, "_is_jupyter", lambda: False)
        viz2 = Visualizer(add_default_axes=False, add_default_grid=False)
        assert viz2._port_conflict_mode is PortConflictMode.ASK

        viz3 = Visualizer(
            add_default_axes=False,
            add_default_grid=False,
            port_conflict_mode=PortConflictMode.CANCEL,
        )
        assert viz3._port_conflict_mode is PortConflictMode.CANCEL
    finally:
        Visualizer.reset()


def test_ask_terminal_prompt_returns_action(monkeypatch):
    viz = Visualizer(add_default_axes=False, add_default_grid=False)

    class _TTY:
        def isatty(self) -> bool:
            return True

    monkeypatch.setattr(sys, "stdin", _TTY())
    monkeypatch.setattr("builtins.input", lambda *_: "a")
    assert viz._ask_port_conflict(8765, []) is PortConflictMode.AUTO

    monkeypatch.setattr("builtins.input", lambda *_: "k")
    assert viz._ask_port_conflict(8765, []) is PortConflictMode.KILL

    monkeypatch.setattr("builtins.input", lambda *_: "c")
    assert viz._ask_port_conflict(8765, []) is PortConflictMode.CANCEL


def test_ask_terminal_prompt_non_tty_cancels(monkeypatch):
    viz = Visualizer(add_default_axes=False, add_default_grid=False)

    class _Pipe:
        def isatty(self) -> bool:
            return False

    monkeypatch.setattr(sys, "stdin", _Pipe())
    assert viz._ask_port_conflict(8765, []) is PortConflictMode.CANCEL
