# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""VisualizerApp — base class for interactive 3D visualization applications.

Derive from :class:`VisualizerApp`, override :meth:`init` and
:meth:`cleanup`, and call :meth:`run` from your ``main()`` function.
"""

from __future__ import annotations

import asyncio
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .camera import CameraConfig, View2DConfig, View3dConfig


class VisualizerApp:
    """Base class for interactive 3D visualization apps.

    Handles the server lifecycle (start → init → wait → cleanup → stop)
    so that derived classes only need to define ``init()`` and ``cleanup()``.

    The :attr:`viz` attribute is a :class:`~pytanga.viz.Visualizer` instance
    that is available to all methods.

    Usage::

        from pytanga.viz._controls import ControlEvent

        class MyApp(VisualizerApp):
            def __init__(self):
                super().__init__(title="My Scene")
                self._data = []

            async def init(self) -> None:
                self.viz.add(...)
                self.viz.add_slider("x", on_change=self.on_x)

            async def on_x(self, value: float, event: ControlEvent) -> None:
                self.viz.update_entity("ent", ...)
                self.viz.flush()

        if __name__ == "__main__":
            MyApp().run()
    """

    def __init__(
        self,
        *,
        port: int | None = None,
        host: str | None = None,
        open_browser: bool | None = None,
        reuse_existing: bool = True,
        title: str = "Tanga 3D Viewer",
        annotation: str | None = None,
        background_color: str = "#1a1a2e",
        camera: CameraConfig | View2DConfig | View3dConfig | None = None,
        space_dim: int | None = None,  # 2 or 3; None = deduce from camera
        enable_server_stop_key: bool = False,
    ) -> None:
        """Create the app and the underlying :class:`~pytanga.viz.Visualizer`.

        Parameters are forwarded directly to :class:`~pytanga.viz.Visualizer`.
        See its documentation for details.
        """
        from .visualizer import Visualizer

        self.viz = Visualizer(
            port=port,
            host=host,
            open_browser=open_browser,
            reuse_existing=reuse_existing,
            title=title,
            annotation=annotation,
            background_color=background_color,
            camera=camera,
            space_dim=space_dim,
            enable_server_stop_key=enable_server_stop_key,
        )
        self._stop_requested = threading.Event()

    # ── lifecycle hooks (override in subclass) ──────────────

    async def init(self) -> None:
        """Called after the server has started.

        Override to add entities, register controls, and push the
        initial scene state.  Default implementation is a no-op.
        """

    async def cleanup(self) -> None:
        """Called once shutdown has been requested, before the server stops.

        Shutdown is requested by terminal Ctrl+C, the browser Ctrl+Q key (when
        enabled), or :meth:`request_shutdown`.  Override for graceful teardown
        (save state, close resources, …).  Default implementation is a no-op.
        """

    # ── app runner ──────────────────────────────────────────

    def request_shutdown(self) -> None:
        """Request that the app shut down.

        Callable from any context — including an async control or interaction
        handler (e.g. a "Quit" button) — to end :meth:`run`.  The event loop
        unblocks, :meth:`cleanup` runs, and the server stops.  Also sets the
        underlying :class:`~pytanga.viz.Visualizer` shutdown event so any
        running :meth:`~pytanga.viz.Visualizer.animate` loop ends as well.
        """
        self._stop_requested.set()
        shutdown = getattr(self.viz, "_shutdown_requested", None)
        if shutdown is not None:
            shutdown.set()

    def _is_stop_requested(self) -> bool:
        """Return ``True`` once shutdown has been requested.

        Shutdown is requested by terminal Ctrl+C / SIGTERM, the browser Ctrl+Q
        server-stop key, or an explicit :meth:`request_shutdown` call.
        """
        if self._stop_requested.is_set():
            return True
        shutdown = getattr(self.viz, "_shutdown_requested", None)
        return shutdown is not None and shutdown.is_set()

    def run(self, *, wait_for_browser: bool = True, timeout: float = 30.0) -> None:
        """Start the server, run :meth:`init`, block until shutdown, then
        run :meth:`cleanup` and stop the server.

        Shutdown is requested by terminal Ctrl+C, the browser Ctrl+Q key (when
        the app was created with ``enable_server_stop_key=True``), or an
        explicit :meth:`request_shutdown` call (e.g. from a control handler).

        Parameters
        ----------
        wait_for_browser:
            If ``True`` (the default), block until at least one browser
            tab connects before calling :meth:`init`.
        timeout:
            Seconds to wait for a browser connection.  Only used when
            ``wait_for_browser=True``.
        """
        ok = self.viz.show(wait_for_browser=wait_for_browser)
        if not ok:
            raise RuntimeError(
                "Server failed to start or no browser connected "
                f"within {timeout}s.  Open {self.viz.url} manually."
            )
        try:
            asyncio.run(self._app_main())
        except KeyboardInterrupt:
            pass
        finally:
            self.viz.stop_server()
            try:
                from rich.console import Console
                from rich.text import Text

                Console().print(Text("Visualizer shut down.", style="dim"))
            except Exception:
                print("Visualizer shut down.")

    async def _app_main(self) -> None:
        """Core asyncio body: init → block until shutdown → cleanup."""
        import logging

        # 1. User setup
        try:
            await self.init()
        except Exception:
            logging.getLogger(__name__).exception("Error in app.init()")
            raise

        # 2. Block until shutdown is requested (Ctrl+C, Ctrl+Q, or
        #    request_shutdown()), or the task is cancelled.
        try:
            while not self._is_stop_requested():
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            pass

        # 3. Teardown
        try:
            await self.cleanup()
        except Exception:
            logging.getLogger(__name__).exception("Error in app.cleanup()")
