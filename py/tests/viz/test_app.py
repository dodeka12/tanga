# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for VisualizerApp shutdown (Ctrl+Q forwarding and request_shutdown())."""

import asyncio
import threading

from pytanga.viz import VisualizerApp


class _RecordingApp(VisualizerApp):
    """VisualizerApp subclass that records whether its lifecycle hooks ran."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.init_called = False
        self.cleanup_called = False

    async def init(self) -> None:
        self.init_called = True

    async def cleanup(self) -> None:
        self.cleanup_called = True


class TestVisualizerAppShutdown:
    def test_constructor_forwards_enable_server_stop_key(self):
        app = VisualizerApp(enable_server_stop_key=True)
        assert app.viz._server_stop_configs[""] == {
            "enabled": True,
            "key": "q",
            "modifiers": ["ctrl"],
        }

    def test_constructor_default_does_not_enable_server_stop_key(self):
        app = VisualizerApp()
        assert "" not in app.viz._server_stop_configs

    def test_request_shutdown_sets_app_flag_and_viz_event(self):
        app = VisualizerApp()
        app.viz._shutdown_requested = threading.Event()
        app.request_shutdown()
        assert app._stop_requested.is_set()
        assert app.viz._shutdown_requested.is_set()

    def test_request_shutdown_is_safe_before_server_start(self):
        app = VisualizerApp()
        app.request_shutdown()  # no _shutdown_requested attribute yet
        assert app._stop_requested.is_set()

    def test_is_stop_requested_false_initially(self):
        app = VisualizerApp()
        assert app._is_stop_requested() is False

    def test_is_stop_requested_true_after_request_shutdown(self):
        app = VisualizerApp()
        app.request_shutdown()
        assert app._is_stop_requested() is True

    def test_is_stop_requested_true_when_viz_shutdown_requested(self):
        app = VisualizerApp()
        app.viz._shutdown_requested = threading.Event()
        app.viz._shutdown_requested.set()
        assert app._is_stop_requested() is True

    def test_app_main_runs_init_and_cleanup_when_stop_requested(self):
        app = _RecordingApp()
        app._stop_requested.set()
        asyncio.run(app._app_main())
        assert app.init_called is True
        assert app.cleanup_called is True

    def test_app_main_returns_when_viz_shutdown_requested(self):
        app = _RecordingApp()
        app.viz._shutdown_requested = threading.Event()
        app.viz._shutdown_requested.set()
        asyncio.run(app._app_main())
        assert app.init_called is True
        assert app.cleanup_called is True
