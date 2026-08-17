# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""SceneExporter — exports a ``Visualizer``'s scene to HTML, glTF, or figures."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytanga.viz.export._animation_recording import AnimationRecording
    from pytanga.viz.visualizer import Visualizer

from pytanga.viz._figure import FigureConfig
from pytanga.viz._styles import AnimStyle as _AS
from pytanga.viz._styles import FigureStyle as _FS


class SceneExporter:
    """Exports a Visualizer's scene to HTML, glTF, or presentation figures.

    Usage::

        from pytanga.viz import SceneExporter

        exporter = SceneExporter(viz)
        exporter.export_html("scene.html")
        exporter.export_figure("figure.html", style=FigureStyle(width=1024))
        exporter.open_figure()
    """

    def __init__(self, visualizer: Visualizer) -> None:
        self._viz = visualizer
        self._default_figure_style = _FS(
            width=800,
            height=600,
            background="transparent",
            auto_rotate=False,
            show_title=True,
            show_annotation=True,
            border_radius="0",
        )
        self._default_anim_style = _AS(
            fps=30,
            loop=True,
            show_controls=True,
            compress=False,
        )
        self._figure_config: FigureConfig | None = None

    # ── Properties ──────────────────────────────────────────────

    @property
    def default_figure_style(self) -> _FS:
        """Mutable canonical ``FigureStyle`` for this exporter."""
        return self._default_figure_style

    @property
    def figure_config(self) -> FigureConfig:
        """Lazy-initialized ``FigureConfig``, inherits from visualizer."""
        if self._figure_config is None:
            self._figure_config = FigureConfig(
                title=self._viz._title,
                annotation=self._viz._annotation,
                footer=self._viz._annotation,
            )
        return self._figure_config

    # ── Path resolution ────────────────────────────────────────

    @staticmethod
    def _resolve_export_path(path: str | Path, extension: str) -> Path:
        """Resolve *path* to an absolute file path, adding *extension* if missing.

        - Relative paths are resolved against the current working directory.
        - ``~`` is expanded to the user's home directory.
        - If the last component has no suffix, *extension* is appended
          (e.g. ``"scene"`` → ``"scene.html"``).
        - Parent directories are created automatically.
        - Raises :exc:`IsADirectoryError` if the resolved path points to
          an existing directory.
        """
        p = Path(path).expanduser()
        if not p.is_absolute():
            p = Path.cwd() / p
        if not p.suffix:
            p = p.with_suffix(extension)
        if p.is_dir():
            raise IsADirectoryError(f"Export path {p} is a directory, not a file.")
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    # ── HTML / glTF ────────────────────────────────────────────

    def export_html(self, path: str | Path, *, overwrite: bool = False) -> None:
        """Export the current scene as a self-contained HTML file.

        The resulting file can be opened by double-clicking — no Python
        server or internet connection needed (Three.js loads from CDN).

        Args:
            path: Output file path (e.g., ``"scene.html"``).  Relative
                paths are resolved against the current working directory.
                If no extension is given, ``.html`` is appended.
            overwrite: If ``False`` (default), raise :exc:`FileExistsError`
                when the target file already exists.
        """
        path = self._resolve_export_path(path, ".html")
        if not overwrite and path.exists():
            raise FileExistsError(
                f"File {path} already exists. Use overwrite=True to replace it."
            )

        from pytanga.viz.export import render_export_html  # noqa: PLC0415

        objects = self._viz._scene.full_state(styles_map=self._viz._default_styles)
        html = render_export_html(objects, self._viz._config.to_dict())
        path.write_text(html, encoding="utf-8")

    def export_glb(self, path: str | Path, *, overwrite: bool = False) -> None:
        """Export the current scene as a glTF 2.0 binary (``.glb``) file.

        The resulting file can be opened in Blender, macOS Preview,
        Windows 3D Viewer, ``<model-viewer>``, or any glTF-compatible tool.

        Args:
            path: Output file path (e.g., ``"scene.glb"``).  Relative
                paths are resolved against the current working directory.
                If no extension is given, ``.glb`` is appended.
            overwrite: If ``False`` (default), raise :exc:`FileExistsError`
                when the target file already exists.
        """
        path = self._resolve_export_path(path, ".glb")
        if not overwrite and path.exists():
            raise FileExistsError(
                f"File {path} already exists. Use overwrite=True to replace it."
            )

        from pytanga.viz.export import build_gltf_scene  # noqa: PLC0415

        all_objects = self._viz._scene.full_state(styles_map=self._viz._default_styles)
        entities = [o for o in all_objects if o.get("layer") != "overlay"]
        glb_data = build_gltf_scene(entities, self._viz._config)
        path.write_bytes(glb_data)

    # ── Figure ─────────────────────────────────────────────────

    def export_figure(
        self,
        path: str | Path,
        *,
        style: _FS | None = None,
        overwrite: bool = False,
    ) -> None:
        """Export the scene as an HTML snippet for embedding in presentations.

        The output is a ``<div>`` + ``<script type="module">`` block — no
        ``<html>``, no ``<head>``, no global style resets.  Paste it directly
        into a reveal.js, Slidev, or Marp slide.

        Args:
            path: Output file path (e.g. ``"figure.html"``).
            style: Optional ``FigureStyle``.  Non-``None`` fields override
                ``default_figure_style``.
            overwrite: If ``False``, raise on existing file.
        """
        path = self._resolve_export_path(path, ".html")
        if not overwrite and path.exists():
            raise FileExistsError(
                f"File {path} already exists. Use overwrite=True to replace it."
            )

        snippet = self.export_figure_html(style=style)
        path.write_text(snippet, encoding="utf-8")

    def export_figure_html(
        self,
        *,
        style: _FS | None = None,
    ) -> str:
        """Return the figure export as an HTML snippet string.

        Args:
            style: Optional ``FigureStyle``.  Non-``None`` fields override
                ``default_figure_style``.

        Returns:
            HTML snippet (``<div>`` + ``<script>``) suitable for direct
            inclusion in a presentation slide.
        """
        from pytanga.viz.export._figure_html import (
            render_export_figure,  # noqa: PLC0415
        )

        # Resolve style: user's non-None fields overlay canonical defaults
        if style is not None:
            resolved = _FS()
            for fld_name, fld_val in self._default_figure_style.__dict__.items():
                setattr(resolved, fld_name, fld_val)
            for fld_name, fld_val in style.__dict__.items():
                if fld_val is not None:
                    setattr(resolved, fld_name, fld_val)
        else:
            resolved = self._default_figure_style

        objects = self._viz._scene.full_state(styles_map=self._viz._default_styles)
        fig_config = self.figure_config

        return render_export_figure(
            objects,
            self._viz._config.to_dict(),
            resolved.to_dict(),
            fig_config.to_dict(),
        )

    def open_figure(
        self,
        *,
        style: _FS | None = None,
    ) -> None:
        """Open a standalone browser window sized to the figure dimensions.

        The window shows only the 3D figure — no browser chrome.

        Args:
            style: Optional ``FigureStyle``.  Non-``None`` fields override
                ``default_figure_style``.
        """
        import tempfile as _tempfile
        import webbrowser as _webbrowser

        if style is not None:
            resolved = _FS()
            for fld_name, fld_val in self._default_figure_style.__dict__.items():
                setattr(resolved, fld_name, fld_val)
            for fld_name, fld_val in style.__dict__.items():
                if fld_val is not None:
                    setattr(resolved, fld_name, fld_val)
        else:
            resolved = self._default_figure_style

        snippet = self.export_figure_html(style=style)

        # Wrap in a minimal full HTML page for standalone viewing
        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self._viz._title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ display: flex; justify-content: center; align-items: center;
         min-height: 100vh; background: #111; }}
</style>
</head>
<body>
  {snippet}
</body>
</html>"""

        with _tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write(full_html)
            tmp_path = f.name

        _webbrowser.open(f"file://{tmp_path}")

    # ── Screenshot & frame capture ───────────────────────

    def screenshot(
        self,
        path: str | Path,
        *,
        width: int | None = None,
        height: int | None = None,
        timeout: float = 5.0,
    ) -> None:
        """Request a screenshot from the live viewer and save as PNG.

        Sends a screenshot request over WebSocket.  The browser captures
        its WebGL canvas and sends the base64-encoded PNG back.  Blocks
        up to *timeout* seconds.

        Requires the WebSocket server to be running
        (``viz.start()`` or ``viz.run()`` must have been called).

        Args:
            path: Output file path (e.g. ``"figure.png"``).
            width: Optional canvas width override.  ``None`` = current size.
            height: Optional canvas height override.
            timeout: Maximum time to wait for the browser response.

        Raises:
            RuntimeError: If the server is not running.
            TimeoutError: If the browser doesn't respond in time.
        """
        if self._viz._server is None or self._viz._loop is None:
            raise RuntimeError(
                "Server is not running. Call viz.start() or viz.run() first."
            )

        from ._screenshot import _request_screenshot_bytes

        png_bytes = _request_screenshot_bytes(
            self._viz._server,
            self._viz._loop,
            width=width,
            height=height,
            timeout=timeout,
        )

        p = self._resolve_export_path(path, ".png")
        p.write_bytes(png_bytes)

    def start_capture(
        self,
        *,
        folder: str | Path | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        """Begin capturing frames to an image sequence.

        Creates *folder* (or a temp directory if ``None``) and initialises a
        frame counter at 0.

        Args:
            folder: Directory to store frame PNGs.  If ``None``, a temporary
                directory is created.
            width: Renderer width override for all frames.
            height: Renderer height override for all frames.

        Raises:
            RuntimeError: If the server is not running.
            RuntimeError: If already capturing.
        """
        if self._viz._server is None or self._viz._loop is None:
            raise RuntimeError(
                "Server is not running. Call viz.start() or viz.run() first."
            )

        from ._capture import FrameCapture

        self._capture = FrameCapture(self._viz._server, self._viz._loop)
        self._capture.start(folder=folder, width=width, height=height)

    def capture_frame(self, *, timeout: float = 5.0) -> Path:
        """Capture a single frame and save as ``frame_NNNN.png``.

        Returns:
            Path to the written PNG file.

        Raises:
            RuntimeError: If :meth:`start_capture` was not called first.
            TimeoutError: If the browser doesn't respond in time.
        """
        if not hasattr(self, "_capture") or self._capture is None:
            raise RuntimeError("Not capturing. Call start_capture() first.")
        return self._capture.capture(timeout=timeout)

    def finish_capture(
        self,
        *,
        video_path: str | Path | None = None,
        fps: int = 30,
        crf: int = 23,
        keep_images: bool = False,
        overwrite: bool = False,
    ) -> Path | None:
        """Finish frame capture and optionally create an MP4 video.

        Args:
            video_path: Output MP4 path (e.g. ``"animation.mp4"``).
                If ``None``, no video is created — frames are left on disk.
            fps: Frame rate for the output video.
            crf: ffmpeg quality (0–51, lower = better, 23 = default).
            keep_images: If ``True``, frame PNGs are kept after video
                creation.  If ``False`` (default), temp folders are deleted
                after successful encoding.  User-specified folders are
                never deleted.
            overwrite: If ``False`` (default), raise :exc:`FileExistsError`
                when the video file already exists.

        Returns:
            Path to the video file, or ``None`` if *video_path* was not given.

        Raises:
            RuntimeError: If :meth:`start_capture` was not called first.
            RuntimeError: If ffmpeg is not found on PATH.
            FileExistsError: If *video_path* already exists and
                *overwrite* is ``False``.
        """
        if not hasattr(self, "_capture") or self._capture is None:
            raise RuntimeError("Not capturing. Call start_capture() first.")
        result = self._capture.finish(
            video_path=video_path,
            fps=fps,
            crf=crf,
            keep_images=keep_images,
            overwrite=overwrite,
        )
        self._capture = None

        # Restore browser renderer to full viewport size and refresh the view.
        # Schedule on the event loop and wait for delivery before returning,
        # so that a subsequent viz.stop() doesn't tear down the server first.
        if self._viz._server is not None and self._viz._loop is not None:
            import asyncio
            import json
            import threading

            done = threading.Event()

            async def _restore_and_refresh() -> None:
                try:
                    await self._viz._server.push_raw(
                        json.dumps({"type": "restore_size"})
                    )
                    # Re-send the scene config to force a full re-render
                    cfg = self._viz._config.to_dict()
                    await self._viz._server.push_raw(json.dumps(cfg))
                finally:
                    done.set()

            asyncio.run_coroutine_threadsafe(_restore_and_refresh(), self._viz._loop)
            if not done.wait(timeout=3.0):
                raise TimeoutError("Browser did not acknowledge restore_size in time")

        return result

    # ── Animated export ────────────────────────────────────

    def start_animation_recording(self) -> AnimationRecording:
        """Begin recording entity state for animated HTML export.

        Returns an ``AnimationRecording`` context object.  Call
        ``capture_frame()`` on it inside the animation loop, then
        pass it to ``export_animated_figure()`` or
        ``export_animated_html()``.

        Usage::

            recording = exporter.start_animation_recording()
            for frame in range(150):
                viz.update_entity(...)
                viz.flush()
                recording.capture_frame()
            exporter.export_animated_figure("anim.html", recording, fps=30)
        """
        from pytanga.viz.export._animation_recording import AnimationRecording

        return AnimationRecording(
            self._viz._scene,
            styles_map=self._viz._default_styles,
        )

    def export_animated_figure(
        self,
        path: str | Path,
        recording,
        *,
        style: _FS | None = None,
        anim_style: _AS | None = None,
        overwrite: bool = False,
    ) -> None:
        """Export a recorded animation as an HTML snippet for embedding.

        The resulting file is a ``<div>`` + ``<script type="module">``
        block — no ``<html>``, no ``<head>``, no global style resets.
        Paste it directly into a reveal.js, Slidev, or Marp slide.

        This is the animated equivalent of ``export_figure()``.

        Args:
            path: Output file path (e.g. ``"animation.html"``).
            recording: The ``AnimationRecording`` from
                ``start_animation_recording()``.
            style: Optional ``FigureStyle``.
            anim_style: Optional ``AnimStyle`` (fps, loop, show_controls,
                compress).  Non-``None`` fields are merged over the
                exporter's ``_default_anim_style``.
            overwrite: If ``False``, raise on existing file.
        """
        from pytanga.viz.export._animated_figure import (
            render_export_animated_figure,
        )

        path = self._resolve_export_path(path, ".html")
        if not overwrite and path.exists():
            raise FileExistsError(
                f"File {path} already exists. Use overwrite=True to replace it."
            )

        if recording.frame_count == 0:
            raise ValueError(
                "Recording is empty. Call recording.capture_frame() at "
                "least once before exporting."
            )

        # Resolve figure style
        if style is not None:
            resolved_style = _FS()
            for fld_name, fld_val in self._default_figure_style.__dict__.items():
                setattr(resolved_style, fld_name, fld_val)
            for fld_name, fld_val in style.__dict__.items():
                if fld_val is not None:
                    setattr(resolved_style, fld_name, fld_val)
        else:
            resolved_style = self._default_figure_style

        # Resolve anim style
        if anim_style is not None:
            resolved_anim = _AS()
            for fld_name, fld_val in self._default_anim_style.__dict__.items():
                setattr(resolved_anim, fld_name, fld_val)
            for fld_name, fld_val in anim_style.__dict__.items():
                if fld_val is not None:
                    setattr(resolved_anim, fld_name, fld_val)
        else:
            resolved_anim = self._default_anim_style

        html = render_export_animated_figure(
            recording.to_dict(),
            figure_style=resolved_style.to_dict(),
            figure_config=self.figure_config.to_dict(),
            anim_style=resolved_anim.to_dict(),
        )
        path.write_text(html, encoding="utf-8")

    def export_animated_html(
        self,
        path: str | Path,
        recording,
        *,
        anim_style: _AS | None = None,
        overwrite: bool = False,
    ) -> None:
        """Export a recorded animation as a standalone full-page HTML document.

        The resulting file is a complete HTML document (``<!DOCTYPE html>``,
        ``<html>``, ``<head>``, ``<body>``) — double-click to open in any
        browser.  The Three.js canvas fills the entire viewport.

        This is the animated equivalent of ``export_html()``.

        Args:
            path: Output file path (e.g. ``"animation.html"``).
            recording: The ``AnimationRecording`` from
                ``start_animation_recording()``.
            anim_style: Optional ``AnimStyle`` (fps, loop, show_controls,
                compress).  Non-``None`` fields are merged over the
                exporter's ``_default_anim_style``.
            overwrite: If ``False``, raise on existing file.
        """
        from pytanga.viz.export._animated_figure import (
            render_export_animated_html,
        )

        path = self._resolve_export_path(path, ".html")
        if not overwrite and path.exists():
            raise FileExistsError(
                f"File {path} already exists. Use overwrite=True to replace it."
            )

        if recording.frame_count == 0:
            raise ValueError(
                "Recording is empty. Call recording.capture_frame() at "
                "least once before exporting."
            )

        # Resolve anim style
        if anim_style is not None:
            resolved_anim = _AS()
            for fld_name, fld_val in self._default_anim_style.__dict__.items():
                setattr(resolved_anim, fld_name, fld_val)
            for fld_name, fld_val in anim_style.__dict__.items():
                if fld_val is not None:
                    setattr(resolved_anim, fld_name, fld_val)
        else:
            resolved_anim = self._default_anim_style

        html = render_export_animated_html(
            recording.to_dict(),
            scene_config=self._viz._config.to_dict(),
            anim_style=resolved_anim.to_dict(),
            title=self._viz._title,
        )
        path.write_text(html, encoding="utf-8")
