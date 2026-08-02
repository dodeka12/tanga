# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Thread-safe screenshot request helper.

Bridges the user's main thread and the server's asyncio event loop.
"""

from __future__ import annotations

import asyncio
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytanga.viz.server import VizServer


def _request_screenshot_bytes(
    server: VizServer,
    event_loop: asyncio.AbstractEventLoop,
    *,
    width: int | None = None,
    height: int | None = None,
    timeout: float = 5.0,
) -> bytes:
    """Request a screenshot from the browser and return raw PNG bytes.

    Schedules the ``request_screenshot`` coroutine on the server's event
    loop (which runs in a background daemon thread) and blocks the calling
    thread until the result is available.

    Args:
        server: The ``VizServer`` instance.
        event_loop: The server's asyncio event loop.
        width: Optional canvas width override.
        height: Optional canvas height override.
        timeout: Seconds to wait for the browser's response.

    Returns:
        Raw PNG image bytes.

    Raises:
        RuntimeError: If the server is not running or no browser is connected.
        TimeoutError: If no response arrives within *timeout* seconds.
    """
    result_container: dict[str, object] = {}
    error_container: dict[str, Exception] = {}
    done_event = threading.Event()

    async def _capture() -> None:
        try:
            png_bytes = await server.request_screenshot(
                width=width, height=height, timeout=timeout
            )
            result_container["data"] = png_bytes
        except Exception as e:
            error_container["error"] = e
        finally:
            done_event.set()

    future = asyncio.run_coroutine_threadsafe(_capture(), event_loop)

    # Wait for completion or timeout (add 1s buffer for scheduling overhead)
    if not done_event.wait(timeout=timeout + 1.0):
        future.cancel()
        raise TimeoutError(f"Screenshot request timed out after {timeout}s")

    if "error" in error_container:
        raise error_container["error"]

    return result_container["data"]  # type: ignore[return-value]
