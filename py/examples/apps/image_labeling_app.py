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

The reusable piece is :class:`ImageLabeler` — a self-contained image-labeling
pane (toolbar + canvas + shape state) that can be embedded in any layout or
``SplitView`` pane.  :class:`ImageLabelingApp` is a thin shell that adds the File
menu and the labelme file handling around it.

Run with:  uv run python py/examples/apps/image_labeling_app.py [labels.json]

Keywords: image, labeling, labelme, app, ActRectangle2D, ActCircle, ActLine, DragPreview, menu
"""

from __future__ import annotations

import argparse
import math
import os
from dataclasses import replace
from typing import Any, Callable, cast

import numpy as np
from pytanga.geometry import Circle, Direction, Ellipse, Line, Point, Rectangle2D
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
    Color,
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
    LabelShape,
    LineStyle,
    MenuView,
    MouseButton,
    PointPath,
    PointPathStyle,
    Rectangle2DStyle,
    Size,
    SquarePointStyle,
    StackView,
    ToolbarView,
    VisualizerApp,
)

_W, _H = 320, 200
_FILL = "#ff4444"
_SELECTED_COLOR = "#ffff44"
_DEFAULT_LABEL = "object"

#: Draw modes that use a drag gesture (``point`` uses a click instead).
_DRAG_MODES = ("rect", "ellipse", "circle", "line", "polygon")


def _gradient(width: int, height: int) -> np.ndarray:
    """A 3-channel RGB gradient of shape (H, W, 3), dtype uint8."""
    ys, xs = np.mgrid[0:height, 0:width]
    r = (xs / max(width - 1, 1) * 255).astype(np.uint8)
    g = (ys / max(height - 1, 1) * 255).astype(np.uint8)
    b = np.full_like(r, 128)
    return np.stack([r, g, b], axis=-1)


class ImageLabeler:
    """A reusable image-labeling pane: a toolbar over an image canvas, plus the
    shape/selection state.

    Owns an :class:`~pytanga.viz.ImageCanvas`, the drawing-tool toolbar, and the
    list of :class:`~pytanga.viz.LabelShape` entries.  :attr:`view` is a
    :class:`~pytanga.viz.StackView` (toolbar above the canvas) to drop straight
    into any layout or ``SplitView`` pane::

        labeler = ImageLabeler(viz)
        layout = SplitView("horizontal", [labeler.view, other_view])

    The menu bar is deliberately **not** part of this class — the host app builds
    its own menu and wires it to :meth:`load` / :meth:`save` / :meth:`to_document`.

    Copy this class into your app and adapt :meth:`_style_for_act` /
    :meth:`_style_for_mode` to change how each shape type is styled.
    """

    def __init__(
        self,
        viz: Any,
        *,
        toolbar: bool = True,
        default_label: str = _DEFAULT_LABEL,
        fill_color: str = _FILL,
        selected_color: str = _SELECTED_COLOR,
        on_change: Callable[[], None] | None = None,
        on_select: Callable[[Any | None], None] | None = None,
    ) -> None:
        self.viz = viz
        self.default_label = default_label
        self.fill_color = fill_color
        self.selected_color = selected_color
        self._on_change = on_change
        self._on_select = on_select

        self.mode: str | None = None
        self.shapes: list[LabelShape] = []
        self.selected: Any = None
        self._store = LabelMeStore()

        # Screen-space handle markers keep a constant on-screen size under zoom.
        self._handle_style = CirclePointStyle(
            size=6.0, thickness=2.0, screen_space=True
        )
        self._vertex_style = CirclePointStyle(
            color=Color.RED, size=6.0, thickness=2.0, screen_space=True
        )
        self._end_handle_style = CirclePointStyle(
            color=Color.GREEN, size=6.0, thickness=2.0, screen_space=True
        )

        # Resize clamp, expressed as a half-extent in canvas pixels (the 2D
        # canvas maps 1 world unit = 1 pixel).  ``None`` max = unbounded.
        self._min_half_px: float | None = 0.5
        self._max_half_px: float | None = None

        self._drag_binding = DragBinding(MouseButton.LEFT, self._on_drag, enabled=False)
        self._canvas = ImageCanvas(
            viz,
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

        # World units per image pixel (identity for the 2D canvas).
        self._pixel_scale = self._canvas.surface.mapper.world_units_per_pixel()

        self._tool_buttons = self._build_tool_buttons()
        self._previews = self._build_previews()

        toolbar_view = (
            ToolbarView(list(self._tool_buttons.values()), border=False)
            if toolbar
            else None
        )
        canvas_view = self._canvas.scene_view()
        canvas_view.preferred_height = Size.fr(1)
        # Fill the leftover space when embedded in a flow container (a vertical
        # StackView here, or a SplitView pane).
        self.view = StackView(
            "vertical",
            [v for v in (toolbar_view, canvas_view) if v is not None],
            fill=True,
        )

    # ── Public accessors ────────────────────────────────────

    @property
    def canvas(self) -> ImageCanvas:
        """The underlying :class:`~pytanga.viz.ImageCanvas`."""
        return self._canvas

    @property
    def handle(self) -> Any:
        """The :class:`~pytanga.viz.VizSceneHandle` the shapes live on."""
        return self._canvas.handle

    def set_image(self, image: ImageData) -> None:
        """Set the background image from an :class:`~pytanga.viz.ImageData`."""
        self._canvas.set_image(image)

    def set_image_file(self, path: str) -> None:
        """Set the background image from an image file on disk (if readable)."""
        arr = self._read_image_file(path)
        if arr is not None:
            self._canvas.set_image(ImageData("image", data=arr))

    # ── Toolbar ─────────────────────────────────────────────

    def _build_tool_buttons(self) -> dict[str, ButtonView]:
        def _tool_button(cid: str, icon: str, tooltip: str) -> ButtonView:
            async def on_click(_value, _event: ControlEvent) -> None:  # noqa: ANN001
                self.set_mode(cid if self.mode != cid else None)

            return ButtonView(
                cid, icon=icon, icon_only=True, tooltip=tooltip, on_click=on_click
            )

        return {
            "rect": _tool_button(
                "rect", "material:crop_square", "Add rectangle (drag)"
            ),
            "ellipse": _tool_button(
                "ellipse", "material:app_badging", "Add ellipse (drag)"
            ),
            "circle": _tool_button("circle", "material:circle", "Add circle (drag)"),
            "line": _tool_button("line", "material:diagonal_line", "Add line (drag)"),
            "polygon": _tool_button(
                "polygon", "material:gesture", "Add polygon (drag; Ctrl+drag extends)"
            ),
            "point": _tool_button("point", "material:place", "Add point (click)"),
        }

    def _build_previews(self) -> dict[str, DragPreview]:
        select = self._make_select_handler()
        return {
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

    # ── Mode + selection ────────────────────────────────────

    def set_mode(self, mode: str | None) -> None:
        """Arm/disarm a draw mode: toggle the drag handler, cursor, and button."""
        self.mode = mode
        self._drag_binding.enabled = mode in _DRAG_MODES
        self._canvas.set_click_enabled(mode == "point")
        self._canvas.set_enabled(mode is not None)
        self._canvas.set_cursor("crosshair" if mode else None)
        for cid, button in self._tool_buttons.items():
            button.set_selected(cid == mode)

    def _make_select_handler(self) -> Any:
        async def on_click(_event, act) -> None:  # noqa: ANN001
            self._select(act)

        return on_click

    def _select(self, act: Any) -> None:
        if self.selected is act:
            return
        self._deselect()
        self.selected = act
        self._set_extra_handles(act, True)
        for shape in self.shapes:
            if shape.act is act:
                self._canvas.handle.update_style(
                    shape.act.entity_id,
                    replace(cast(Any, shape.style), color=self.selected_color),
                )
                break
        self._canvas.handle.flush()
        self._notify_select(act)

    def _deselect(self) -> None:
        if self.selected is None:
            return
        act = self.selected
        self._set_extra_handles(act, False)
        for shape in self.shapes:
            if shape.act is act:
                self._canvas.handle.update_style(
                    shape.act.entity_id, cast(Any, shape.style)
                )
                break
        self._canvas.handle.flush()
        self.selected = None
        self._notify_select(None)

    async def _on_delete(self, _event) -> None:  # noqa: ANN001
        if self.selected is None:
            return
        act = self.selected
        self.selected = None
        self.shapes = [s for s in self.shapes if s.act is not act]
        act.remove()
        self._canvas.handle.flush()
        self._notify_change()
        self._notify_select(None)

    async def _on_escape(self, _event) -> None:  # noqa: ANN001
        self._deselect()
        for preview in self._previews.values():
            preview.discard()

    # ── Drag-to-create ──────────────────────────────────────

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
        self.add_shape(act)
        if self.mode == "polygon":
            self.set_mode(None)  # one-shot

    async def _on_click(self, event, _canvas: ImageCanvas) -> None:  # noqa: ANN001
        if self.mode != "point":
            return
        pos = event.world_position
        act = ActPoint(
            pos.x,
            pos.y,
            0.0,
            on_click=self._make_select_handler(),
        )
        self.add_shape(act)

    # ── Shapes ──────────────────────────────────────────────

    def _act_from_entity(self, entity: Any) -> Any:
        """Wrap a plain labelme entity in an interactive act (click-to-select)."""
        select = self._make_select_handler()
        if isinstance(entity, Rectangle2D):
            return ActRectangle2D(
                center=entity.center,
                size=entity.size,
                angle=entity.angle,
                on_click=select,
                handle_style=self._handle_style,
            )
        if isinstance(entity, Ellipse):
            du = entity.dir_u if entity.dir_u is not None else Direction(1.0, 0.0, 0.0)
            angle = math.atan2(du.y, du.x)
            return ActEllipse(
                center=entity.center,
                radius_u=entity.radius_u,
                radius_v=entity.radius_v,
                angle=angle,
                on_click=select,
                handle_style=self._handle_style,
            )
        if isinstance(entity, Circle):
            return ActCircle(
                center=entity.center,
                radius=entity.radius,
                on_click=select,
                handle_style=self._handle_style,
            )
        if isinstance(entity, Line):
            return ActLine(
                start=entity.start,
                end=entity.end,
                on_click=select,
                handle_style=self._handle_style,
            )
        if isinstance(entity, PointPath):
            pts = [Point(x, y, z) for x, y, z in entity.points]
            closed = len(pts) > 1 and pts[0] == pts[-1]
            if closed:
                pts = pts[:-1]
            return ActPolygon(
                pts,
                closed=closed,
                on_click=select,
                handle_style=self._vertex_style,
                end_handle_style=self._end_handle_style,
            )
        if isinstance(entity, Point):
            return ActPoint(entity, on_click=select)
        raise TypeError(f"unsupported labelme entity: {type(entity).__name__}")

    def _apply_size_limits(self, act: Any) -> None:
        """Clamp resize to the app's pixel-derived limits (half-extent)."""
        act.set_pixel_scale(self._pixel_scale)
        if isinstance(act, ActRectangle2D):
            act.set_size_limits(
                None if self._min_half_px is None else 2.0 * self._min_half_px,
                None if self._max_half_px is None else 2.0 * self._max_half_px,
            )
        elif isinstance(act, (ActCircle, ActEllipse)):
            act.set_radius_limits(self._min_half_px, self._max_half_px)

    def add_shape(self, act: Any, label: str | None = None) -> None:
        """Register *act* as a labeled shape, styled for its type."""
        style = self._style_for_act(act)
        self._canvas.handle.add(act, style=style)
        self._apply_size_limits(act)
        self._set_extra_handles(act, False)
        self.shapes.append(
            LabelShape(
                act=act,
                style=style,
                label=label if label is not None else self.default_label,
            )
        )
        self._canvas.handle.flush()
        self._notify_change()

    def clear_shapes(self) -> None:
        """Remove every labeled shape (and clear the selection)."""
        self._deselect()
        for shape in self.shapes:
            shape.act.remove()
        self.shapes = []
        self._canvas.handle.flush()
        self._notify_change()

    # ── labelme load/save ───────────────────────────────────

    def load(self, path: str) -> None:
        """Load *path* — a labelme ``.json`` file, or a bare image file."""
        if os.path.splitext(path)[1].lower() != ".json":
            self.clear_shapes()
            self.set_image_file(path)
            return
        result = self._store.load(path)
        for message in result.errors:
            print(f"labelme: skipped {message}")
        self.load_document(result.document, path)

    def load_document(self, doc: LabelMeDocument, json_path: str = "") -> None:
        """Replace the current shapes with those from *doc* (and its image)."""
        self.clear_shapes()
        self._load_document_image(doc, json_path)
        objs, errors = self._store.iter_objects(doc)
        for message in errors:
            print(f"labelme: skipped {message}")
        for entity, label in objs:
            self.add_shape(self._act_from_entity(entity), label=label)

    def save(self, path: str | os.PathLike[str]) -> None:
        """Write the current shapes to *path* as labelme JSON."""
        self._store.save(self.to_document(image_path=str(path)), path)

    def to_document(self, *, image_path: str = "") -> LabelMeDocument:
        """Export the current shapes as a :class:`~pytanga.viz.LabelMeDocument`."""
        return LabelMeDocument(
            shapes=self._store.shapes_from_objects(
                [(s.act.entity, s.label) for s in self.shapes]
            ),
            image_path=image_path,
        )

    def _load_document_image(self, doc: LabelMeDocument, json_path: str) -> None:
        arr = None
        if doc.image_path:
            candidate = os.path.join(os.path.dirname(json_path), doc.image_path)
            arr = self._read_image_file(candidate)
        if arr is None and doc.image_data:
            arr = self._read_image_bytes(doc.image_data)
        if arr is not None:
            self._canvas.set_image(ImageData("image", data=arr))

    @staticmethod
    def _read_image_file(path: str) -> np.ndarray | None:
        try:
            from PIL import Image

            return np.asarray(Image.open(path).convert("RGB"))
        except Exception:
            return None

    @staticmethod
    def _read_image_bytes(data: str) -> np.ndarray | None:
        try:
            import base64
            import io

            from PIL import Image

            raw = base64.b64decode(data)
            return np.asarray(Image.open(io.BytesIO(raw)).convert("RGB"))
        except Exception:
            return None

    # ── Styles + callbacks ──────────────────────────────────

    @staticmethod
    def _set_extra_handles(act: Any, visible: bool) -> None:
        """Toggle the optional translate/rotate handles on a composite shape."""
        if hasattr(act, "set_translate_handle_visible"):
            act.set_translate_handle_visible(visible)
        if hasattr(act, "set_rotate_handle_visible"):
            act.set_rotate_handle_visible(visible)

    def _style_for_act(self, act: Any) -> Any:
        if isinstance(act, ActRectangle2D):
            return Rectangle2DStyle(color=self.fill_color, fill=True, fill_opacity=0.15)
        if isinstance(act, ActEllipse):
            return EllipseStyle(color=self.fill_color, fill=True, fill_opacity=0.15)
        if isinstance(act, ActCircle):
            return CircleStyle(
                color=self.fill_color, thickness=2, fill=True, fill_opacity=0.15
            )
        if isinstance(act, ActLine):
            return LineStyle(color=self.fill_color, thickness=2)
        if isinstance(act, ActPolygon):
            return PointPathStyle(color=self.fill_color, line_thickness=2)
        return SquarePointStyle(color=self.fill_color, size=1.5, thickness=2)

    def _style_for_mode(self, mode: str) -> Any:
        if mode == "rect":
            return Rectangle2DStyle(color=self.fill_color, fill=True, fill_opacity=0.15)
        if mode == "ellipse":
            return EllipseStyle(color=self.fill_color, fill=True, fill_opacity=0.15)
        if mode == "circle":
            return CircleStyle(
                color=self.fill_color, thickness=2, fill=True, fill_opacity=0.15
            )
        if mode == "line":
            return LineStyle(color=self.fill_color, thickness=2)
        if mode == "polygon":
            return PointPathStyle(color=self.fill_color, line_thickness=2)
        return SquarePointStyle(color=self.fill_color, size=1.5, thickness=2)

    def _notify_change(self) -> None:
        if self._on_change is not None:
            self._on_change()

    def _notify_select(self, act: Any | None) -> None:
        if self._on_select is not None:
            self._on_select(act)


class ImageLabelingApp(VisualizerApp):
    """A thin app shell: an :class:`ImageLabeler` plus a File menu and file path."""

    def __init__(self, file_path: str | None = None) -> None:
        super().__init__(
            title="Tanga — Image Labeling",
            space_dim=2,
            add_default_axes=False,
            add_default_grid=False,
        )
        self._file_path = file_path
        self._labeler = ImageLabeler(self.viz)
        self._layout = self._build_layout()

    def _build_layout(self) -> StackView:
        return StackView(
            "vertical",
            [self._build_menu(), self._labeler.view],
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

    # ── App lifecycle ───────────────────────────────────────

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

    # ── File handling ───────────────────────────────────────

    def _load(self, path: str) -> None:
        self._labeler.load(path)
        self._file_path = path

    def _save(self) -> None:
        if self._file_path is None:
            print("No file path — use Save As…")
            return
        self._labeler.save(self._file_path)

    async def _show_open_dialog(self) -> None:
        async def _on_file(path: str, _event: ControlEvent) -> None:
            self._load(path)

        await self.viz.show_dialog_async(
            FileChooserDialog(
                "open_file",
                on_accept=_on_file,
                file_filter=".json, .jpg, .jpeg, .png",
            ),
            title="Open labelme JSON or image",
        )

    async def _show_save_dialog(self) -> None:
        async def _on_file(path: str, _event: ControlEvent) -> None:
            if os.path.splitext(path)[1] == "":
                path += ".json"
            self._file_path = path
            self._save()

        await self.viz.show_dialog_async(
            FileChooserDialog(
                "save_file",
                on_accept=_on_file,
                existing_only=False,
                file_filter=".json",
            ),
            title="Save labelme JSON",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Label images in labelme format.")
    parser.add_argument(
        "file", nargs="?", default=None, help="labelme JSON file to load on start"
    )
    args = parser.parse_args()
    ImageLabelingApp(file_path=args.file).run()


if __name__ == "__main__":
    main()
