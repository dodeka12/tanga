# Label images in the labelme JSON format

**Keywords:** image · labeling · labelme · app · ActRectangle2D · ActCircle · ActLine · DragPreview · menu

A `~pytanga.viz.VisualizerApp` that shows an image and a toolbar of
drawing tools (rectangle, ellipse, circle, line, polygon, point).  Drag to
create rectangle/ellipse/circle/line shapes; click-drag a polygon to start an
open two-vertex segment (Ctrl+drag a vertex to extend it, drag an endpoint onto
the other to close it); click to place a point.  Click a shape to select it;
Delete/Backspace removes the selection.  A File menu (Open…/Save/Save As…/Exit)
and a command-line path argument load/save labelme JSON.

## Run

```bash
uv run python py/examples/apps/image_labeling_app.py
```

## Source

[`apps/image_labeling_app.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/apps/image_labeling_app.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""image_labeling_app.py — Label images in the labelme JSON format.

A :class:`~pytanga.viz.VisualizerApp` that shows an image and a toolbar of
drawing tools (rectangle, ellipse, circle, line, polygon, point).  Drag to
create rectangle/ellipse/circle/line shapes; click-drag a polygon to start an
open two-vertex segment (Ctrl+drag a vertex to extend it, drag an endpoint onto
the other to close it); click to place a point.  Click a shape to select it;
Delete/Backspace removes the selection.  A File menu (Open…/Save/Save As…/Exit)
and a command-line path argument load/save labelme JSON.

Run with:  uv run python py/examples/apps/image_labeling_app.py [labels.json]

Keywords: image, labeling, labelme, app, ActRectangle2D, ActCircle, ActLine, DragPreview, menu
"""

from __future__ import annotations

import argparse
from dataclasses import replace

import numpy as np
from pytanga.viz import (
    ActCircle,
    ActEllipse,
    ActLine,
    ActPoint,
    ActPolygon,
    ActRectangle2D,
    ButtonView,
    CirclePointStyle,
    CircleStyle,
    ControlEvent,
    DragBinding,
    DragEvent,
    DragPreview,
    EllipseStyle,
    FileChooserDialog,
    ImageCanvas,
    ImageData,
    LabelMeDocument,
    LabelMeStore,
    LineStyle,
    MenuView,
    MouseButton,
    PointPathStyle,
    Rectangle2DStyle,
    Size,
    SplitView,
    SquarePointStyle,
    ToolbarView,
    VisualizerApp,
)

_W, _H = 320, 200
_FILL = "#ff4444"
_SELECTED_COLOR = "#ffff44"
_DEFAULT_LABEL = "object"


def _gradient(width: int, height: int) -> np.ndarray:
    """A 3-channel RGB gradient of shape (H, W, 3), dtype uint8."""
    ys, xs = np.mgrid[0:height, 0:width]
    r = (xs / max(width - 1, 1) * 255).astype(np.uint8)
    g = (ys / max(height - 1, 1) * 255).astype(np.uint8)
    b = np.full_like(r, 128)
    return np.stack([r, g, b], axis=-1)


class ImageLabelingApp(VisualizerApp):
    """Draws, selects, deletes, and loads/saves labelme shapes on an image."""

    def __init__(self, file_path: str | None = None) -> None:
        super().__init__(
            title="Tanga — Image Labeling",
            space_dim=2,
            add_default_axes=False,
            add_default_grid=False,
        )
        self._file_path = file_path
        self.mode: str | None = None
        self.shapes: list[tuple[object, object, str]] = []  # (act, style, label)
        self.selected: object | None = None
        self._store = LabelMeStore()
        self._handle_style = CirclePointStyle(size=1.0, thickness=2.0)
        self._vertex_style = CirclePointStyle(color="#ff4444", size=1.0, thickness=2.0)
        self._end_handle_style = CirclePointStyle(
            color="#00cc44", size=1.0, thickness=2.0
        )

        self._drag_binding = DragBinding(MouseButton.LEFT, self._on_drag, enabled=False)
        self._canvas = ImageCanvas(
            self.viz,
            drag_handlers=[self._drag_binding],
            on_drag_start=self._on_drag_start,
            on_drag_end=self._on_drag_end,
            on_click=self._on_click,
        )
        self._canvas.set_image(ImageData("gradient", data=_gradient(_W, _H)))
        self._canvas.set_enabled(False)
        self._canvas.on_key("Delete", self._on_delete)
        self._canvas.on_key("Backspace", self._on_delete)
        self._canvas.on_key("Escape", self._on_escape)

        self._build_tools()
        self._layout = self._build_layout()

    # ── Toolbar / layout ───────────────────────────────────

    def _build_tools(self) -> None:
        def _tool_button(cid: str, icon: str, tooltip: str) -> ButtonView:
            async def on_click(_value, _event: ControlEvent) -> None:  # noqa: ANN001
                self.set_mode(cid if self.mode != cid else None)

            return ButtonView(
                cid, icon=icon, icon_only=True, tooltip=tooltip, on_click=on_click
            )

        self._tool_buttons = {
            "rect": _tool_button("rect", "material:crop_square", "Add rectangle (drag)"),
            "ellipse": _tool_button("ellipse", "material:circle", "Add ellipse (drag)"),
            "circle": _tool_button("circle", "material:circle", "Add circle (drag)"),
            "line": _tool_button("line", "material:show_chart", "Add line (drag)"),
            "polygon": _tool_button(
                "polygon", "material:gesture", "Add polygon (drag; Ctrl+drag extends)"
            ),
            "point": _tool_button("point", "material:place", "Add point (click)"),
        }

        select = self._make_select_handler()
        self._previews: dict[str, DragPreview] = {
            "rect": DragPreview(
                self._canvas.handle,
                factory=ActRectangle2D,
                style=self._style_for_mode("rect"),
                factory_kwargs={"on_click": select, "handle_style": self._handle_style},
            ),
            "ellipse": DragPreview(
                self._canvas.handle,
                factory=ActEllipse,
                style=self._style_for_mode("ellipse"),
                factory_kwargs={"on_click": select, "handle_style": self._handle_style},
            ),
            "circle": DragPreview(
                self._canvas.handle,
                factory=ActCircle,
                style=self._style_for_mode("circle"),
                factory_kwargs={"on_click": select, "handle_style": self._handle_style},
            ),
            "line": DragPreview(
                self._canvas.handle,
                factory=ActLine,
                style=self._style_for_mode("line"),
                factory_kwargs={"on_click": select, "handle_style": self._handle_style},
            ),
            "polygon": DragPreview(
                self._canvas.handle,
                factory=ActPolygon,
                style=self._style_for_mode("polygon"),
                factory_kwargs={
                    "on_click": select,
                    "handle_style": self._vertex_style,
                    "end_handle_style": self._end_handle_style,
                },
            ),
        }

    def _build_layout(self) -> SplitView:
        toolbar = ToolbarView(list(self._tool_buttons.values()), border=False)
        return SplitView(
            "vertical",
            sizes=[Size.px(40), Size.px(40), Size.fr(1)],
            children=[self._build_menu(), toolbar, self._canvas.scene_view()],
        )

    def _build_menu(self) -> MenuView:
        async def _on_open(_value, _event: ControlEvent) -> None:  # noqa: ANN001
            await self._show_open_dialog()

        async def _on_save(_value, _event: ControlEvent) -> None:  # noqa: ANN001
            self._save()

        async def _on_save_as(_value, _event: ControlEvent) -> None:  # noqa: ANN001
            await self._show_save_dialog()

        async def _on_exit(_value, _event: ControlEvent) -> None:  # noqa: ANN001
            self.request_shutdown()

        return MenuView(
            mode="bar",
            children=[
                MenuView(
                    "File",
                    [
                        ButtonView("open", label="Open…", on_click=_on_open),
                        ButtonView("save", label="Save", on_click=_on_save),
                        ButtonView("save_as", label="Save As…", on_click=_on_save_as),
                        ButtonView("exit", label="Exit", on_click=_on_exit),
                    ],
                ),
            ],
        )

    # ── App lifecycle ──────────────────────────────────────

    async def init(self) -> None:
        if self._file_path is not None:
            self._load(self._file_path)

    def run(
        self,
        *,
        wait_for_browser: bool = True,
        timeout: float = 30.0,
        port: int | None = None,
        host: str | None = None,
    ) -> None:
        import asyncio

        ok = self.viz.show(
            layout=self._layout,
            wait_for_browser=wait_for_browser,
            timeout=timeout,
            port=port,
            host=host,
        )
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

    # ── Mode + selection ───────────────────────────────────

    def set_mode(self, mode: str | None) -> None:
        """Arm/disarm a draw mode: toggle the drag handler, cursor, and button."""
        self.mode = mode
        self._drag_binding.enabled = mode in ("rect", "ellipse", "circle", "line", "polygon")
        self._canvas.set_click_enabled(mode == "point")
        self._canvas.set_enabled(mode is not None)
        self._canvas.set_cursor("crosshair" if mode else None)
        for cid, button in self._tool_buttons.items():
            button.set_selected(cid == mode)

    def _make_select_handler(self) -> object:
        async def on_click(_event, act) -> None:  # noqa: ANN001
            self._select(act)

        return on_click

    def _select(self, act: object) -> None:
        if self.selected is act:
            return
        self._deselect()
        self.selected = act
        for a, style, _label in self.shapes:
            if a is act:
                self._canvas.handle.update_style(
                    a.entity_id, replace(style, color=_SELECTED_COLOR)
                )
                break
        self._canvas.handle.flush()

    def _deselect(self) -> None:
        if self.selected is None:
            return
        for a, style, _label in self.shapes:
            if a is self.selected:
                self._canvas.handle.update_style(a.entity_id, style)
                break
        self._canvas.handle.flush()
        self.selected = None

    async def _on_delete(self, _event) -> None:  # noqa: ANN001
        if self.selected is None:
            return
        act = self.selected
        self.selected = None
        self.shapes = [(a, s, label) for a, s, label in self.shapes if a is not act]
        act.remove()
        self._canvas.handle.flush()

    async def _on_escape(self, _event) -> None:  # noqa: ANN001
        self._deselect()
        for preview in self._previews.values():
            preview.discard()

    # ── Drag-to-create ─────────────────────────────────────

    async def _on_drag_start(self, event: DragEvent, _canvas: ImageCanvas) -> None:
        preview = self._previews.get(self.mode or "")
        if preview is not None:
            preview.begin(event.world_position)

    async def _on_drag(self, event: DragEvent, _canvas: ImageCanvas) -> bool:
        preview = self._previews.get(self.mode or "")
        if preview is None:
            return False
        if preview.anchor is None:
            preview.begin(event.world_position)
        preview.update(event.world_position)
        return True

    async def _on_drag_end(self, event: DragEvent, _canvas: ImageCanvas) -> None:
        preview = self._previews.get(self.mode or "")
        if preview is None or preview.anchor is None:
            return
        act = preview.finalize(event.world_position)
        self._add_shape(act)
        if self.mode == "polygon":
            self.set_mode(None)  # one-shot

    async def _on_click(self, event, _canvas: ImageCanvas) -> None:  # noqa: ANN001
        if self.mode != "point":
            return
        pos = event.world_position
        act = ActPoint(pos.x, pos.y, 0.0, on_click=self._make_select_handler())
        self._add_shape(act)

    # ── labelme load/save ──────────────────────────────────

    def _load(self, path: str) -> None:
        doc = self._store.load(path)
        self._clear_shapes()
        for obj, label in self._store.iter_objects(doc, active=True):
            self._add_shape(obj, label=label)
        self._file_path = path

    def _save(self) -> None:
        if self._file_path is None:
            print("No file path — use Save As…")
            return
        self._store.save(self._to_document(), self._file_path)

    def _to_document(self) -> LabelMeDocument:
        return LabelMeDocument(
            shapes=self._store.shapes_from_objects(
                [(act, label) for act, _style, label in self.shapes]
            ),
            image_path=self._file_path or "",
        )

    def _clear_shapes(self) -> None:
        self._deselect()
        for act, _style, _label in self.shapes:
            act.remove()
        self.shapes = []
        self._canvas.handle.flush()

    async def _show_open_dialog(self) -> None:
        async def _on_file(path: str, _event: ControlEvent) -> None:
            self._load(path)

        await self.viz.show_dialog_async(
            FileChooserDialog("open_file", on_accept=_on_file),
            title="Open labelme JSON",
        )

    async def _show_save_dialog(self) -> None:
        async def _on_file(path: str, _event: ControlEvent) -> None:
            self._file_path = path
            self._save()

        await self.viz.show_dialog_async(
            FileChooserDialog("save_file", on_accept=_on_file),
            title="Save labelme JSON",
        )

    # ── Helpers ────────────────────────────────────────────

    def _add_shape(self, act: object, label: str = _DEFAULT_LABEL) -> None:
        style = self._style_for_act(act)
        self._canvas.handle.add(act, style=style)
        self.shapes.append((act, style, label))
        self._canvas.handle.flush()

    def _style_for_act(self, act: object) -> object:
        if isinstance(act, ActRectangle2D):
            return Rectangle2DStyle(color=_FILL, fill=True, fill_opacity=0.15)
        if isinstance(act, ActEllipse):
            return EllipseStyle(color=_FILL, fill=True, fill_opacity=0.15)
        if isinstance(act, ActCircle):
            return CircleStyle(color=_FILL, thickness=2)
        if isinstance(act, ActLine):
            return LineStyle(color=_FILL, thickness=2)
        if isinstance(act, ActPolygon):
            return PointPathStyle(color=_FILL, line_thickness=2)
        return SquarePointStyle(color=_FILL, size=1.5, thickness=2)

    def _style_for_mode(self, mode: str) -> object:
        if mode == "rect":
            return Rectangle2DStyle(color=_FILL, fill=True, fill_opacity=0.15)
        if mode == "ellipse":
            return EllipseStyle(color=_FILL, fill=True, fill_opacity=0.15)
        if mode == "circle":
            return CircleStyle(color=_FILL, thickness=2)
        if mode == "line":
            return LineStyle(color=_FILL, thickness=2)
        if mode == "polygon":
            return PointPathStyle(color=_FILL, line_thickness=2)
        return SquarePointStyle(color=_FILL, size=1.5, thickness=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Label images in labelme format.")
    parser.add_argument(
        "file", nargs="?", default=None, help="labelme JSON file to load on start"
    )
    args = parser.parse_args()
    ImageLabelingApp(file_path=args.file).run()


if __name__ == "__main__":
    main()
````
