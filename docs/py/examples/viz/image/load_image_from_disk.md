# Open an image from disk via a File → Open… menu

**Keywords:** image · ImageCanvas · menu · FileChooserDialog · split view · PIL · file open · contrast · EXR · HDR · pyramid · tiled · progress

Shows a red→green→blue placeholder in an `~pytanga.viz.ImageCanvas`
inside a split-view layout.  A `mode="bar"` `~pytanga.viz.MenuView`
holds a `File` sub-menu whose `Open…` item shows a
`~pytanga.viz.FileChooserDialog`; choosing an image loads it — PIL for
common formats, `~pytanga.viz.image.read_exr` for OpenEXR and
`~pytanga.viz.image.read_hdr` for Radiance HDR — and swaps it into the
canvas, while a `~pytanga.viz.LogView` pane reports the path and
dimensions.

Large images (longer side > 4096 px or > 32 MB) are served automatically as an
on-demand tile pyramid, and EXR/HDR loads report their progress to the log.

Hold `Ctrl` and drag with the left mouse button to adjust the image's
brightness (vertical) and contrast (horizontal).

## Run

```bash
uv run python py/examples/viz/image/load_image_from_disk.py
```

## Source

[`viz/image/load_image_from_disk.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/image/load_image_from_disk.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""load_image_from_disk.py — Open an image from disk via a File → Open… menu.

Shows a red→green→blue placeholder in an :class:`~pytanga.viz.ImageCanvas`
inside a split-view layout.  A ``mode="bar"`` :class:`~pytanga.viz.MenuView`
holds a ``File`` sub-menu whose ``Open…`` item shows a
:class:`~pytanga.viz.FileChooserDialog`; choosing an image loads it — PIL for
common formats, :func:`~pytanga.viz.image.read_exr` for OpenEXR and
:func:`~pytanga.viz.image.read_hdr` for Radiance HDR — and swaps it into the
canvas, while a :class:`~pytanga.viz.LogView` pane reports the path and
dimensions.

Large images (longer side > 4096 px or > 32 MB) are served automatically as an
on-demand tile pyramid, and EXR/HDR loads report their progress to the log.

Hold ``Ctrl`` and drag with the left mouse button to adjust the image's
brightness (vertical) and contrast (horizontal).

Run with:  uv run python py/examples/viz/image/load_image_from_disk.py

Keywords: image, ImageCanvas, menu, FileChooserDialog, split view, PIL, file open, contrast, EXR, HDR, pyramid, tiled, progress
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import numpy as np
from pytanga.viz import (
    ButtonView,
    ControlEvent,
    DragBinding,
    DragEvent,
    FileChooserDialog,
    ImageCanvas,
    ImageData,
    LogView,
    MenuView,
    ModifierKey,
    MouseButton,
    SplitView,
    StackView,
    Visualizer,
)
from pytanga.viz.image import pil_to_numpy, read_exr, read_hdr

_WIDTH, _HEIGHT = 320, 200


def _gradient(width: int, height: int) -> np.ndarray:
    """A 3-channel RGB gradient of shape (H, W, 3), dtype uint8.

    Red at top-left → green at the centre → blue at bottom-right.
    """
    ys, xs = np.mgrid[0:height, 0:width]
    t = (xs + ys) / max(width + height - 2, 1)
    r = np.zeros_like(t)
    g = np.zeros_like(t)
    b = np.zeros_like(t)
    lo = t <= 0.5
    r[lo] = (1.0 - 2.0 * t[lo]) * 255
    g[lo] = (2.0 * t[lo]) * 255
    hi = ~lo
    g[hi] = (2.0 - 2.0 * t[hi]) * 255
    b[hi] = (2.0 * t[hi] - 1.0) * 255
    return np.stack([r, g, b], axis=-1).astype(np.uint8)


def _load(path: str, *, on_progress: Any = None) -> np.ndarray:
    """Load *path* as a numpy pixel buffer (PIL, OpenEXR, or Radiance HDR)."""
    from PIL import Image

    suffix = Path(path).suffix.lower()
    if suffix == ".exr":
        return read_exr(path, on_progress=on_progress)
    if suffix in (".hdr", ".pic"):
        return read_hdr(path, on_progress=on_progress)

    with Image.open(path) as img:
        img.load()
        # Convert exotic modes (palette/CMYK/…) so pixels map to 1/3/4 channels.
        if img.mode not in ("L", "RGB", "RGBA", "I;16", "F"):
            img = img.convert("RGB")
        return pil_to_numpy(img)


async def on_drag(event: DragEvent, canvas: ImageCanvas) -> bool:
    # Ctrl+left drag: horizontal movement → contrast, vertical → brightness.
    dx, dy = event.delta_pixels
    u = canvas.image_view.uniforms
    canvas.set_uniform("u_contrast", max(0.0, u["u_contrast"] + 0.005 * dx))
    canvas.set_uniform("u_brightness", u["u_brightness"] + 0.005 * dy)
    return True


viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
canvas = ImageCanvas(
    viz,
    drag_handlers=[DragBinding(MouseButton.LEFT, on_drag, ModifierKey.CTRL)],
)
canvas.set_image(ImageData("image", data=_gradient(_WIDTH, _HEIGHT)))
log = LogView(id="log", max_history=100)
log.log("Choose File → Open… to load an image.")

_dialog_id: str | None = None


async def _on_file(path: str, _event: ControlEvent) -> None:
    loop = asyncio.get_running_loop()
    last_tens = -1

    def _report_progress(fraction: float) -> None:
        nonlocal last_tens
        tens = int(fraction * 10)
        if tens != last_tens:
            last_tens = tens
            loop.call_soon_threadsafe(
                log.log,
                {"message": f"Loading {path}… {int(fraction * 100)}%", "level": "info"},
            )

    try:
        log.log({"message": f"Loading {path}…", "level": "info"})
        data = await asyncio.to_thread(_load, path, on_progress=_report_progress)
        image = ImageData("image", data=data)
        canvas.set_image(image)
        channels = data.shape[2] if data.ndim == 3 else 1
        transport = "tiled" if image.source == "tiled" else "full frame"
        log.log({"message": f"Loaded {path}", "level": "info"})
        log.log(
            f"{data.shape[1]} × {data.shape[0]} px, {channels} channel(s), {transport}"
        )
        if Path(path).suffix.lower() in (".exr", ".hdr", ".pic"):
            log.log(
                "HDR values > 1 clamp for display; raise u_value_max or use a custom shader."
            )
    except Exception as exc:  # noqa: BLE001 - surface any load failure in the pane
        log.log({"message": f"Failed to load {path}: {exc}", "level": "error"})


async def _on_open(_value: Any, _event: ControlEvent) -> None:
    global _dialog_id
    if _dialog_id:
        viz.remove_dialog(_dialog_id)
    _dialog_id = await viz.show_dialog_async(
        FileChooserDialog(
            "open_file",
            on_accept=_on_file,
            file_filter="*.png, *.jpg, *.exr",
            folders_only=False,
        ),
        title="Open image",
    )


bar = MenuView(
    mode="bar",
    children=[
        MenuView(
            "File",
            [ButtonView("file_open", label="Open…", on_click=_on_open)],
        ),
    ],
)

viz.show(
    layout=StackView(
        "vertical",
        [
            bar,
            SplitView("horizontal", [canvas.scene_view(), log]),
        ],
    )
)
viz.wait()
````
