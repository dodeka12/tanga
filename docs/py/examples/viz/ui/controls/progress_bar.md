# Determinate and indeterminate progress bars with a status line

**Keywords:** progress bar · control · determinate · indeterminate · VisualizerApp

A `ProgressBarView` with a `total` shows a determinate bar that fills as
`value` advances; with `indeterminate=True` it shows an
animated bar for "something is running".  `title` renders above the bar and
`text` renders a status line below it.  Press **Start** to run a simulated
download and start the scan; it stops when it finishes, or early via
**Stop scan**.

## Run

```bash
uv run python py/examples/viz/ui/controls/progress_bar.py
```

## Source

[`viz/ui/controls/progress_bar.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/ui/controls/progress_bar.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""progress_bar.py — Determinate and indeterminate progress bars with a status line.

A ``ProgressBarView`` with a ``total`` shows a determinate bar that fills as
``value`` advances; with ``indeterminate=True`` it shows an
animated bar for "something is running".  ``title`` renders above the bar and
``text`` renders a status line below it.  Press **Start** to run a simulated
download and start the scan; it stops when it finishes, or early via
**Stop scan**.

Run with:  uv run python py/examples/viz/ui/controls/progress_bar.py

Keywords: progress bar, control, determinate, indeterminate, VisualizerApp
"""

from __future__ import annotations

import asyncio

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    ControlEvent,
    GroupView,
    ProgressBarView,
    SceneView,
    VisualizerApp,
)


class ProgressBarApp(VisualizerApp):
    """A sphere plus two progress bars — one determinate, one indeterminate."""

    def __init__(self) -> None:
        super().__init__(title="Progress Bar")
        self._download: ProgressBarView | None = None
        self._scan: ProgressBarView | None = None
        self._running = False
        self._scan_running = False  # the scan starts stopped and runs on Start

    async def init(self) -> None:
        self.viz.add(
            Sphere(Point(0.0, 0.0, 0.0), radius=1.0),
            entity_id="ball",
            color="#4488ff",
            opacity=0.4,
        )

        self._download = ProgressBarView(
            "download",
            title="Downloading…",
            total=100,
            value=0,
            text="Idle",
        )
        self._scan = ProgressBarView(
            "scan",
            title="Scanning files…",
            indeterminate=False,
            text="Idle",
        )

        self.viz.set_layout(
            SceneView(
                "",
                overlay=[
                    GroupView(
                        "Progress",
                        [
                            self._download,
                            self._scan,
                            ButtonView(
                                "start",
                                label="Start",
                                tooltip="Run the simulated work",
                                on_click=self.on_start,
                            ),
                            ButtonView(
                                "stop_scan",
                                label="Stop scan",
                                tooltip="Stop the scan animation",
                                on_click=self.on_stop_scan,
                            ),
                        ],
                        position="bottom-right",
                    ),
                ],
            )
        )
        self.viz.flush()

    async def on_start(self, _value: None, _event: ControlEvent) -> None:
        if self._running:
            return
        self._running = True

        download = self._download
        scan = self._scan
        assert download is not None and scan is not None

        download.set_progress(0, "Starting…")
        # (Re)start the scan in case it was stopped earlier.
        self._scan_running = True
        scan.set_indeterminate(True)
        scan.set_text("Scanning files…")

        for i in range(1, 101):
            await asyncio.sleep(0.03)
            download.set_progress(i, f"Step {i}/100")
            if self._scan_running and i % 10 == 0:
                scan.set_text(f"Scanned {i} files…")

        download.set_text("Done")
        if self._scan_running:
            self._scan_running = False
            scan.set_indeterminate(False)
            scan.set_text("Finished")
        self._running = False

    async def on_stop_scan(self, _value: None, _event: ControlEvent) -> None:
        if not self._scan_running:
            return
        self._scan_running = False
        scan = self._scan
        assert scan is not None
        scan.set_indeterminate(False)
        scan.set_text("Scan stopped")


if __name__ == "__main__":
    ProgressBarApp().run()
````
