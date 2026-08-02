# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Frame capture state machine for animation recording.

Manages a sequence of PNG frames captured from the live WebSocket viewer,
with optional MP4 video creation via ffmpeg.
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytanga.viz.server import VizServer


def _find_ffmpeg() -> str | None:
    """Return the path to ffmpeg, or ``None`` if not found."""
    return shutil.which("ffmpeg")


class FrameCapture:
    """State machine for capturing sequenced PNG frames.

    Lifecycle: ``IDLE → start() → [capture() × N] → finish() → IDLE``

    Usage::

        cap = FrameCapture(server, loop)
        cap.start()
        for _ in range(90):
            cap.capture(width=800, height=600)
        cap.finish(video_path="anim.mp4", fps=30)
    """

    def __init__(
        self,
        server: VizServer,
        event_loop: asyncio.AbstractEventLoop,
    ) -> None:
        self._server = server
        self._loop = event_loop
        self._folder: Path | None = None
        self._is_temp: bool = False
        self._counter: int = 0
        self._active: bool = False

    # ── State ──────────────────────────────────────────────

    @property
    def is_capturing(self) -> bool:
        """``True`` after :meth:`start` and before :meth:`finish`."""
        return self._active

    @property
    def frame_count(self) -> int:
        """Number of frames captured so far."""
        return self._counter

    @property
    def folder(self) -> Path | None:
        """The folder where frames are stored (only valid while capturing)."""
        return self._folder

    # ── Lifecycle ──────────────────────────────────────────

    def start(
        self,
        *,
        folder: str | Path | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        """Begin capturing frames.

        Args:
            folder: Directory to write frame PNGs.  If ``None``, a temporary
                directory is created (and cleaned up in :meth:`finish` unless
                ``keep_images=True``).
            width: Renderer width override (``None`` = current browser size).
            height: Renderer height override.
        """
        if self._active:
            raise RuntimeError("Already capturing. Call finish_capture() first.")

        if folder is None:
            self._folder = Path(tempfile.mkdtemp(prefix="tanga_capture_"))
            self._is_temp = True
        else:
            p = Path(folder).expanduser()
            if not p.is_absolute():
                p = Path.cwd() / p
            p.mkdir(parents=True, exist_ok=True)
            self._folder = p
            self._is_temp = False

        self._counter = 0
        self._active = True
        self._width = width
        self._height = height

    def capture(self, *, timeout: float = 5.0) -> Path:
        """Capture a single frame and save as ``frame_NNNN.png``.

        Returns:
            Path to the written PNG file.

        Raises:
            RuntimeError: If :meth:`start` has not been called.
        """
        if not self._active:
            raise RuntimeError("Not capturing. Call start_capture() first.")

        from ._screenshot import _request_screenshot_bytes

        png_bytes = _request_screenshot_bytes(
            self._server,
            self._loop,
            width=self._width,
            height=self._height,
            timeout=timeout,
        )

        path = self._folder / f"frame_{self._counter:04d}.png"  # type: ignore[union-attr]
        path.write_bytes(png_bytes)
        self._counter += 1
        return path

    def finish(
        self,
        *,
        video_path: str | Path | None = None,
        fps: int = 30,
        crf: int = 23,
        keep_images: bool = False,
        overwrite: bool = False,
    ) -> Path | None:
        """Stop capturing and optionally create an MP4 video.

        Args:
            video_path: Output MP4 path (e.g. ``"animation.mp4"``).
                If ``None``, frames are left on disk and no video is created.
            fps: Frame rate for the output video.
            crf: ffmpeg quality (0–51, lower = better, 23 = default).
            keep_images: If ``True``, frame PNGs are kept.  If ``False``,
                temp folders are deleted after video creation.  User-specified
                folders are never deleted.
            overwrite: If ``False`` (default), raise :exc:`FileExistsError`
                when the video file already exists.

        Returns:
            Path to the video file, or ``None`` if *video_path* was not given.

        Raises:
            RuntimeError: If ``ffmpeg`` is not found on PATH.
            RuntimeError: If ffmpeg exits with a non-zero code.
            FileExistsError: If *video_path* already exists and
                *overwrite* is ``False``.
        """
        if not self._active:
            raise RuntimeError("Not capturing. Call start_capture() first.")

        self._active = False
        result: Path | None = None

        if video_path is not None:
            ffmpeg = _find_ffmpeg()
            if ffmpeg is None:
                raise RuntimeError(
                    "ffmpeg not found on PATH. Install ffmpeg to create videos:\n"
                    "  Ubuntu/Debian: sudo apt install ffmpeg\n"
                    "  macOS: brew install ffmpeg\n"
                    "  Windows: choco install ffmpeg"
                )

            out = Path(video_path).expanduser()
            if not out.is_absolute():
                out = Path.cwd() / out
            out.parent.mkdir(parents=True, exist_ok=True)

            if not overwrite and out.exists():
                raise FileExistsError(
                    f"File {out} already exists. Use overwrite=True to replace it."
                )

            # ffmpeg expects the pattern relative to the folder
            # -vf pad ensures even dimensions (h264 requirement)
            cmd = [
                ffmpeg,
                "-y",
                "-framerate",
                str(fps),
                "-i",
                "frame_%04d.png",
                "-vf",
                "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                str(crf),
                str(out),
            ]

            proc = subprocess.run(
                cmd,
                cwd=str(self._folder),
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                stderr = proc.stderr.strip()
                raise RuntimeError(
                    f"ffmpeg exited with code {proc.returncode}: {stderr}"
                )
            result = out

        # Clean up temp folder
        if self._is_temp and not keep_images and self._folder is not None:
            shutil.rmtree(self._folder, ignore_errors=True)
        elif self._is_temp and keep_images:
            try:
                from rich.console import Console
                from rich.text import Text

                Console().print(
                    Text.from_markup(
                        f"[dim]Frame images kept in:[/dim] [cyan]{self._folder}[/cyan]"
                    )
                )
            except ImportError:
                print(f"Frame images kept in: {self._folder}")

        return result
