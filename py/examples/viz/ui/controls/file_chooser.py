# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""file_chooser.py — A file chooser with a backend-driven file browser.

Run with:  uv run python py/examples/viz/ui/controls/file_chooser.py

Keywords: controls, file chooser, file browser, VisualizerApp
"""

from __future__ import annotations

from pytanga.geometry import Point
from pytanga.viz import (
    ButtonView,
    ControlEvent,
    FileChooserView,
    GroupView,
    SceneView,
    VisualizerApp,
)


class FileChooserApp(VisualizerApp):
    """A file chooser plus a button that opens the browser from the backend."""

    def __init__(self) -> None:
        super().__init__(title="File Chooser")
        self._last_path = ""

    async def init(self) -> None:
        self.viz.add(Point(0, 0, 0), color="#4488ff")
        self.viz.set_layout(
            SceneView(
                "",
                overlay=[
                    GroupView(
                        "",
                        [
                            FileChooserView(
                                "data_file",
                                label="Data file",
                                placeholder="/path/to/file",
                                on_change=self.on_file,
                            ),
                            ButtonView(
                                "open", label="Open browser", on_click=self.on_open
                            ),
                        ],
                        position="bottom-right",
                    )
                ],
            )
        )
        self.viz.flush()

    async def on_file(self, path: str, _event: ControlEvent) -> None:
        self._last_path = path
        self.viz.set_annotation(f"Selected: `{path}`")

    async def on_open(self, _value: None, _event: ControlEvent) -> None:
        self.viz.open_file_chooser("data_file", path=self._last_path or None)


if __name__ == "__main__":
    FileChooserApp().run()
