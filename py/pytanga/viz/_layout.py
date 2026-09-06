# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Concrete :class:`LayoutHost`: scenes, layouts (base + overlay), serialization."""

from __future__ import annotations

import asyncio
from typing import Any

from ._ports import ServerState
from .views import (
    SceneView,
    StackView,
    View,
    serialize_layout,
)


class OverlayContainer:
    """Everything floating above a layout's base: anchored groups (and later
    draggable dialogs, banners, the editor)."""

    def __init__(
        self,
        sync: Any = None,
        transport: Any = None,
        layout: Any = None,
    ) -> None:
        self._sync = sync or (lambda: None)
        self._transport = transport
        self._layout = layout
        self._global_overlay: list[Any] = []
        self._scene_overlays: dict[str, list[Any]] = {}
        self._injected_overlay_ids: set[int] = set()
        self._banners: dict[str | None, dict[str, Any]] = {}
        self._banner_counter = 0
        self._dialogs: dict[str | None, dict[str, Any]] = {}
        self._dialog_counter = 0

    def configure(self, *, transport: Any = None, layout: Any = None) -> None:
        """Bind the transport/layout-host ports (post-construction wiring)."""
        if transport is not None:
            self._transport = transport
        if layout is not None:
            self._layout = layout

    # ── Mounting ───────────────────────────────────────

    def add(self, view: Any, *, scene: str | None = None, anchor: Any = None) -> None:
        """Mount *view* into the overlay (global or per-scene) and re-sync.

        ``scene`` selects the per-scene overlay (``None``/``\"\"`` = the global
        overlay, floating above every pane).  ``anchor`` sets the view's
        ``position`` when it has one (e.g. a ``GroupView``/``MenuView``).
        """
        if anchor is not None and hasattr(view, "position"):
            view.position = anchor
        scene_name = scene if scene is not None else ""
        if scene_name != "":
            overlays = self._scene_overlays.setdefault(scene_name, [])
            if view not in overlays:
                overlays.append(view)
                self._injected_overlay_ids.add(id(view))
            self._sync()
        else:
            if view not in self._global_overlay:
                self._global_overlay.append(view)
                # Granular: push only the new overlay view (not the whole layout)
                # and refresh the cached layouts for a future full `view_layout`.
                self._layout._reserialize_overlays()
                self._push_overlay_define(view)

    def _push_overlay_define(self, view: Any) -> None:
        """Send a granular ``overlay_define`` for one global-overlay view."""
        self._transport.send({"type": "overlay_define", "view": view._serialize()})

    def remove_view(self, view_id: str, *, scene: str | None = None) -> None:
        """Remove a previously mounted overlay view by its stable ``id``.

        A global view (``scene=None``) is removed with a granular
        ``overlay_remove`` message; a per-scene view is injected into the
        layout's scene panes, so it triggers a full re-sync instead.
        """
        scene_name = scene if scene is not None else ""
        if scene_name != "":
            overlays = self._scene_overlays.get(scene_name, [])
            remaining = [v for v in overlays if getattr(v, "id", None) != view_id]
            if len(remaining) != len(overlays):
                for v in overlays:
                    if getattr(v, "id", None) == view_id:
                        self._injected_overlay_ids.discard(id(v))
                self._scene_overlays[scene_name] = remaining
                self._sync()
        else:
            for view in list(self._global_overlay):
                if getattr(view, "id", None) == view_id:
                    self._global_overlay.remove(view)
                    self._layout._reserialize_overlays()
                    self._push_overlay_remove(view_id)
                    return

    def _push_overlay_remove(self, view_id: str) -> None:
        """Send a granular ``overlay_remove`` for one global-overlay view."""
        self._transport.send({"type": "overlay_remove", "id": view_id})

    # ── Banners ───────────────────────────────────────
    def _next_banner_id(self) -> str:
        """Return a fresh, unique banner id."""
        self._banner_counter += 1
        return f"banner_{self._banner_counter}"

    def _register_banner(
        self,
        text: str,
        *,
        id: str | None,
        title: str,
        align_x: float,
        align_y: float,
        auto_hide: bool,
        dismissable: bool,
        controls: list[Any] | None,
        on_close: Any,
        scene_name: str | None,
    ) -> Any:
        """Create, store, and register a banner; return it (un-pushed)."""
        from ._banner import Banner

        if id is None:
            id = self._next_banner_id()
        else:
            for scoped in self._banners.values():
                if id in scoped:
                    raise ValueError(f"Banner id {id!r} is already in use")

        ctrl_list = list(controls or [])
        banner = Banner(
            id=id,
            text=text,
            title=title,
            align_x=align_x,
            align_y=align_y,
            auto_hide=auto_hide,
            dismissable=dismissable,
            controls=ctrl_list,
            on_close=on_close,
        )
        for ctrl in ctrl_list:
            if getattr(ctrl, "on_click", None) is not None:
                self._transport.register(ctrl.id, ctrl.on_click, event="click")
            elif getattr(ctrl, "on_change", None) is not None:
                self._transport.register(ctrl.id, ctrl.on_change, event="change")
        if on_close is not None:
            self._transport.register(id, on_close, event="close")
        self._banners.setdefault(scene_name, {})[id] = banner
        return banner

    def show_banner(
        self,
        text: str,
        *,
        id: str | None = None,
        title: str = "",
        align_x: float = 0.5,
        align_y: float = 0.5,
        auto_hide: bool = True,
        dismissable: bool = True,
        controls: list[Any] | None = None,
        on_close: Any = None,
        scene_name: str | None = None,
    ) -> str:
        """Show a banner/dialog and return its id.

        A global banner (``scene_name=None``) spans the whole viewport; a
        per-scene banner (``scene_name="<name>"``) is shown inside every pane
        displaying that scene.  ``controls`` is a list of :class:`Button` /
        :class:`Slider` / :class:`Dropdown` objects (the same controls usable
        in a control group) rendered as the banner's options; their
        ``on_click`` / ``on_change`` handlers are registered automatically.
        """
        banner = self._register_banner(
            text,
            id=id,
            title=title,
            align_x=align_x,
            align_y=align_y,
            auto_hide=auto_hide,
            dismissable=dismissable,
            controls=controls,
            on_close=on_close,
            scene_name=scene_name,
        )
        self._push_banner(banner, scene_name)
        return banner.id

    def alert(
        self,
        text: str,
        *,
        title: str = "",
        ok_label: str = "OK",
        on_ok: Any = None,
        align_x: float = 0.5,
        align_y: float = 0.5,
        dismissable: bool = True,
        scene_name: str | None = None,
    ) -> str:
        """Show an acknowledge banner with a single OK button."""
        from ._controls import Button

        bid = self._next_banner_id()
        buttons = [Button(id=f"{bid}_ok", label=ok_label, on_click=on_ok)]
        return self.show_banner(
            text,
            id=bid,
            title=title,
            align_x=align_x,
            align_y=align_y,
            auto_hide=True,
            dismissable=dismissable,
            controls=buttons,
            scene_name=scene_name,
        )

    def confirm(
        self,
        text: str,
        *,
        title: str = "",
        yes_label: str = "Yes",
        no_label: str = "No",
        cancel_label: str = "Cancel",
        on_yes: Any = None,
        on_no: Any = None,
        on_cancel: Any = None,
        align_x: float = 0.5,
        align_y: float = 0.5,
        dismissable: bool = True,
        scene_name: str | None = None,
    ) -> str:
        """Show a yes/no/cancel banner."""
        from ._controls import Button

        bid = self._next_banner_id()
        buttons = [
            Button(id=f"{bid}_yes", label=yes_label, on_click=on_yes),
            Button(id=f"{bid}_no", label=no_label, on_click=on_no),
            Button(id=f"{bid}_cancel", label=cancel_label, on_click=on_cancel),
        ]
        return self.show_banner(
            text,
            id=bid,
            title=title,
            align_x=align_x,
            align_y=align_y,
            auto_hide=True,
            dismissable=dismissable,
            controls=buttons,
            scene_name=scene_name,
        )

    def _unregister_banner(self, banner: Any) -> None:
        """Unregister a banner's control handlers and ``on_close`` handler."""
        for ctrl in banner.controls:
            self._transport.unregister(ctrl.id)
        self._transport.unregister(banner.id, "close")

    def remove_banner(self, banner_id: str, *, scene_name: str | None = None) -> None:
        """Remove a banner by id (and unregister its handlers)."""
        scoped = self._banners.get(scene_name, {})
        banner = scoped.get(banner_id)
        if banner is None:
            return
        self._unregister_banner(banner)
        del scoped[banner_id]
        self._push_banner_remove(banner_id, scene_name)

    def clear_banners(self, *, scene_name: str | None = None) -> None:
        """Remove all banners in a scope (or globally when ``scene_name=None``)."""
        scoped = self._banners.pop(scene_name, {})
        for banner in scoped.values():
            self._unregister_banner(banner)
        self._push_banner_clear(scene_name)

    def _push_banner(self, banner: Any, scene_name: str | None) -> None:
        from ._banner import serialize_banner

        self._transport.send(serialize_banner(banner, scene=scene_name))

    def _push_banner_remove(self, banner_id: str, scene_name: str | None) -> None:
        from ._banner import serialize_banner_remove

        self._transport.send(serialize_banner_remove(banner_id, scene=scene_name))

    def _push_banner_clear(self, scene_name: str | None) -> None:
        from ._banner import serialize_banner_clear

        self._transport.send(serialize_banner_clear(scene=scene_name))

    async def _push_banner_async(self, banner: Any, scene_name: str | None) -> None:
        from ._banner import serialize_banner

        await self._transport.send_async(serialize_banner(banner, scene=scene_name))

    async def _push_banner_remove_async(
        self, banner_id: str, scene_name: str | None
    ) -> None:
        from ._banner import serialize_banner_remove

        await self._transport.send_async(
            serialize_banner_remove(banner_id, scene=scene_name)
        )

    async def _push_banner_clear_async(self, scene_name: str | None) -> None:
        from ._banner import serialize_banner_clear

        await self._transport.send_async(serialize_banner_clear(scene=scene_name))

    async def show_banner_async(
        self,
        text: str,
        *,
        id: str | None = None,
        title: str = "",
        align_x: float = 0.5,
        align_y: float = 0.5,
        auto_hide: bool = True,
        dismissable: bool = True,
        controls: list[Any] | None = None,
        on_close: Any = None,
        scene_name: str | None = None,
    ) -> str:
        """Awaitable :meth:`show_banner` (see its docs).

        Awaits the ``banner_define`` push so the banner is visible before the
        caller proceeds; safe from a handler (on ``self._loop``) or from
        ``init()`` / ``cleanup()`` (user loop).
        """
        banner = self._register_banner(
            text,
            id=id,
            title=title,
            align_x=align_x,
            align_y=align_y,
            auto_hide=auto_hide,
            dismissable=dismissable,
            controls=controls,
            on_close=on_close,
            scene_name=scene_name,
        )
        await self._transport.on_server_loop(
            lambda: self._push_banner_async(banner, scene_name)
        )
        return banner.id

    async def remove_banner_async(
        self, banner_id: str, *, scene_name: str | None = None
    ) -> None:
        """Awaitable :meth:`remove_banner`."""
        scoped = self._banners.get(scene_name, {})
        banner = scoped.get(banner_id)
        if banner is None:
            return
        self._unregister_banner(banner)
        del scoped[banner_id]
        await self._transport.on_server_loop(
            lambda: self._push_banner_remove_async(banner_id, scene_name)
        )

    async def clear_banners_async(self, *, scene_name: str | None = None) -> None:
        """Awaitable :meth:`clear_banners`."""
        scoped = self._banners.pop(scene_name, {})
        for banner in scoped.values():
            self._unregister_banner(banner)
        await self._transport.on_server_loop(
            lambda: self._push_banner_clear_async(scene_name)
        )

    async def _on_banner_close(
        self, target: str | None, value: Any, event: Any
    ) -> None:
        """Handle a ``banner_closed`` event: fire (and consume) the ``on_close`` handler."""
        handler = self._transport.get(target, "close") if target else None
        if handler is None:
            return
        self._transport.unregister(target, "close")
        try:
            await handler(value, event)
        except Exception:
            import logging

            logging.getLogger(__name__).exception(
                "Error in close handler for %r", target
            )

    # ── Dialogs ──────────────────────────────────────
    def _next_dialog_id(self) -> str:
        """Return a fresh, unique dialog id."""
        self._dialog_counter += 1
        return f"dialog_{self._dialog_counter}"

    def _register_dialog(
        self,
        content: Any,
        *,
        id: str | None,
        title: str,
        align_x: float,
        align_y: float,
        dismissable: bool,
        on_close: Any,
        width: Any,
        height: Any,
        scene_name: str | None,
    ) -> Any:
        """Create, store, and register a dialog; return it (un-pushed)."""
        from ._dialog import Dialog, FileChooserDialog
        from .views import View

        if id is None:
            id = self._next_dialog_id()
        else:
            for scoped in self._dialogs.values():
                if id in scoped:
                    raise ValueError(f"Dialog id {id!r} is already in use")

        if isinstance(content, FileChooserDialog):
            dialog = content.build_dialog(id)
            if title:
                dialog.title = title
            if width is not None:
                dialog.width = width
            if height is not None:
                dialog.height = height
            if on_close is not None:
                dialog.on_close = on_close
        elif isinstance(content, View):
            dialog = Dialog(
                id=id,
                content=content,
                title=title,
                align_x=align_x,
                align_y=align_y,
                dismissable=dismissable,
                on_close=on_close,
                width=width,
                height=height,
            )
        else:
            raise TypeError(
                f"content must be a View or FileChooserDialog, got "
                f"{type(content).__name__}"
            )

        # Register the content's control-view handlers, then close/accept callbacks.
        self._layout.register(dialog.content)
        if dialog.on_close is not None:
            self._transport.register(id, dialog.on_close, event="close")
        if dialog.on_accept is not None:
            self._transport.register(id, dialog.on_accept, event="accept")
        self._dialogs.setdefault(scene_name, {})[id] = dialog
        return dialog

    def show_dialog(
        self,
        content: Any,
        *,
        id: str | None = None,
        title: str = "",
        align_x: float = 0.5,
        align_y: float = 0.5,
        dismissable: bool = True,
        on_close: Any = None,
        width: Any = None,
        height: Any = None,
        scene_name: str | None = None,
    ) -> str:
        """Show a dialog and return its id.

        A global dialog (``scene_name=None``) spans the whole viewport; a
        per-scene dialog (``scene_name="<name>"``) is shown inside every pane
        displaying that scene.  ``content`` is any :class:`View` (e.g. a
        :class:`StackView` of ``*View`` control wrappers) rendered inside the
        dialog body, or a :class:`FileChooserDialog` spec; its control-view
        handlers are registered automatically.

        ``width`` / ``height`` optionally size the dialog (``Size.px`` or
        ``Size.percent``); ``None`` shrink-wraps the content.  Closing the
        dialog (the ✕, or a backend ``remove_dialog``) fires ``on_close`` on
        the server loop.  With ``dismissable=False`` the dialog is modal — a
        dimmed backdrop blocks the scene and there is no ✕ (close it via a
        control in ``content`` or ``remove_dialog``).
        """
        dialog = self._register_dialog(
            content,
            id=id,
            title=title,
            align_x=align_x,
            align_y=align_y,
            dismissable=dismissable,
            on_close=on_close,
            width=width,
            height=height,
            scene_name=scene_name,
        )
        self._push_dialog(dialog, scene_name)
        return dialog.id

    def _unregister_dialog(self, dialog: Any) -> None:
        """Unregister a dialog's content control handlers and close/accept callbacks."""
        from .views import iter_control_views

        for view in iter_control_views(dialog.content):
            self._transport.unregister(view.id)
        self._transport.unregister(dialog.id, "close")
        self._transport.unregister(dialog.id, "accept")

    def _find_dialog(self, dialog_id: str) -> tuple[Any, str | None] | None:
        """Return ``(dialog, scene_name)`` for *dialog_id*, or ``None``."""
        for scene_name, scoped in self._dialogs.items():
            if dialog_id in scoped:
                return scoped[dialog_id], scene_name
        return None

    def remove_dialog(self, dialog_id: str, *, scene_name: str | None = None) -> None:
        """Remove a dialog by id (and unregister its handlers)."""
        scoped = self._dialogs.get(scene_name, {})
        dialog = scoped.get(dialog_id)
        if dialog is None:
            return
        self._unregister_dialog(dialog)
        del scoped[dialog_id]
        self._push_dialog_remove(dialog_id, scene_name)

    def clear_dialogs(self, *, scene_name: str | None = None) -> None:
        """Remove all dialogs in a scope (or globally when ``scene_name=None``)."""
        scoped = self._dialogs.pop(scene_name, {})
        for dialog in scoped.values():
            self._unregister_dialog(dialog)
        self._push_dialog_clear(scene_name)

    def _push_dialog(self, dialog: Any, scene_name: str | None) -> None:
        from ._dialog import serialize_dialog

        self._transport.send(serialize_dialog(dialog, scene=scene_name))

    def _push_dialog_remove(self, dialog_id: str, scene_name: str | None) -> None:
        from ._dialog import serialize_dialog_remove

        self._transport.send(serialize_dialog_remove(dialog_id, scene=scene_name))

    def _push_dialog_clear(self, scene_name: str | None) -> None:
        from ._dialog import serialize_dialog_clear

        self._transport.send(serialize_dialog_clear(scene=scene_name))

    async def _push_dialog_async(self, dialog: Any, scene_name: str | None) -> None:
        from ._dialog import serialize_dialog

        await self._transport.send_async(serialize_dialog(dialog, scene=scene_name))

    async def _push_dialog_remove_async(
        self, dialog_id: str, scene_name: str | None
    ) -> None:
        from ._dialog import serialize_dialog_remove

        await self._transport.send_async(
            serialize_dialog_remove(dialog_id, scene=scene_name)
        )

    async def _push_dialog_clear_async(self, scene_name: str | None) -> None:
        from ._dialog import serialize_dialog_clear

        await self._transport.send_async(serialize_dialog_clear(scene=scene_name))

    async def show_dialog_async(
        self,
        content: Any,
        *,
        id: str | None = None,
        title: str = "",
        align_x: float = 0.5,
        align_y: float = 0.5,
        dismissable: bool = True,
        on_close: Any = None,
        width: Any = None,
        height: Any = None,
        scene_name: str | None = None,
    ) -> str:
        """Awaitable :meth:`show_dialog` (see its docs)."""
        dialog = self._register_dialog(
            content,
            id=id,
            title=title,
            align_x=align_x,
            align_y=align_y,
            dismissable=dismissable,
            on_close=on_close,
            width=width,
            height=height,
            scene_name=scene_name,
        )
        await self._transport.on_server_loop(
            lambda: self._push_dialog_async(dialog, scene_name)
        )
        return dialog.id

    async def remove_dialog_async(
        self, dialog_id: str, *, scene_name: str | None = None
    ) -> None:
        """Awaitable :meth:`remove_dialog`."""
        scoped = self._dialogs.get(scene_name, {})
        dialog = scoped.get(dialog_id)
        if dialog is None:
            return
        self._unregister_dialog(dialog)
        del scoped[dialog_id]
        await self._transport.on_server_loop(
            lambda: self._push_dialog_remove_async(dialog_id, scene_name)
        )

    async def clear_dialogs_async(self, *, scene_name: str | None = None) -> None:
        """Awaitable :meth:`clear_dialogs`."""
        scoped = self._dialogs.pop(scene_name, {})
        for dialog in scoped.values():
            self._unregister_dialog(dialog)
        await self._transport.on_server_loop(
            lambda: self._push_dialog_clear_async(scene_name)
        )

    async def _on_dialog_accept(self, target: str | None, event: Any) -> None:
        """Handle an ``accept`` event: fire ``on_accept`` and remove the dialog."""
        found = self._find_dialog(target) if target else None
        if found is None:
            return
        dialog, scene_name = found
        value = None
        if dialog.control_id:
            ctrl = self._layout.resolve_control(dialog.control_id)
            if ctrl is not None:
                value = ctrl.get_value()
        handler = self._transport.get(target, "accept")
        if handler is not None:
            self._transport.unregister(target, "accept")
            try:
                await handler(value, event)
            except Exception:
                import logging

                logging.getLogger(__name__).exception(
                    "Error in accept handler for %r", target
                )
        self.remove_dialog(target, scene_name=scene_name)

    async def _on_dialog_close(
        self, target: str | None, value: Any, event: Any
    ) -> None:
        """Handle a dialog ``close`` event: fire ``on_close`` and remove the dialog."""
        handler = self._transport.get(target, "close") if target else None
        if handler is not None:
            self._transport.unregister(target, "close")
            try:
                await handler(value, event)
            except Exception:
                import logging

                logging.getLogger(__name__).exception(
                    "Error in close handler for %r", target
                )
        found = self._find_dialog(target) if target else None
        if found is not None:
            self.remove_dialog(target, scene_name=found[1])

    # ── Editor ───────────────────────────────────────
    def open_editor(
        self,
        cid: str,
        *,
        label: str = "",
        value: str = "",
        on_close: Any = None,
    ) -> str:
        """Open a transient multi-line text editor in the viewer overlay.

        When the editor is closed, *on_close* (an async ``(text, event)``
        callable) is invoked on the server loop with the edited text, or
        ``None`` when the edit is discarded (✕).  The editor is one-shot: the
        handler is consumed after it runs.
        """
        self._transport.register(cid, on_close, event="close")
        self._push_editor_define(cid, label=label, value=value)
        return cid

    def _push_editor_define(self, cid: str, *, label: str, value: str) -> None:
        """Push the ``editor_define`` message that opens the editor."""
        self._transport.send(
            {
                "type": "editor_define",
                "id": cid,
                "label": label,
                "value": value,
            }
        )

    async def _on_editor_close(
        self, target: str | None, value: Any, event: Any
    ) -> None:
        """Handle an ``editor_closed`` event: fire (and consume) the ``on_close`` handler."""
        handler = self._transport.get(target, "close") if target else None
        if handler is None:
            return
        self._transport.unregister(target, "close")
        try:
            await handler(value, event)
        except Exception:
            import logging

            logging.getLogger(__name__).exception(
                "Error in close handler for %r", target
            )


class Layout:
    """A named layout: a base view tree + an overlay container."""

    def __init__(self, base: View, overlay: OverlayContainer) -> None:
        self.base = base
        self.overlay = overlay


class LayoutHostImpl:
    """Owns the scenes and the layouts (each a base + overlay) and serialization."""

    def __init__(
        self,
        state: ServerState,
        scene_factory: Any,
        transport: Any = None,
        client_log: Any = None,
    ) -> None:
        self._state = state
        self._scene_factory = scene_factory
        self._transport = transport
        self._client_log = client_log
        self._layout_control_ids: set[str] = set()
        self._scenes: dict[str, Any] = {}
        self._overlay = OverlayContainer(
            sync=self._sync_overlays, transport=transport, layout=self
        )
        self._layouts: dict[str, Layout] = {}
        self._layouts_serialized: dict[str, dict[str, Any]] = {}
        self._scene_layouts_serialized: dict[str, dict[str, Any]] = {}

    # ── LayoutHost contract ─────────────────────────────

    def scene(self, name: str) -> Any:
        return self._scenes[name]

    def scene_names(self) -> list[str]:
        return list(self._scenes.keys())

    def add_scene(self, name: str, space_dim: int | None = None) -> Any:
        """Create a scene + an auto single-``SceneView`` layout (raise if name taken)."""
        if name in self._scenes or name in self._layouts:
            raise ValueError(f"Scene or layout {name!r} already exists")
        scene = self._scene_factory(name, space_dim)
        self._scenes[name] = scene
        self._layouts[name] = Layout(
            StackView("vertical", [SceneView(name)]), self._overlay
        )
        return scene

    @property
    def scenes(self) -> dict[str, Any]:
        return self._scenes

    def __getitem__(self, name: str) -> Layout:
        return self._layouts[name]

    @property
    def base(self) -> View:
        return self[""].base

    @property
    def overlay(self) -> OverlayContainer:
        return self[""].overlay

    def set_layout(self, root: View, name: str = "") -> str:
        """Register (or replace) the base view tree for *name*; return it.

        Registers the subtree's control handlers, injects push callbacks, and
        re-syncs the serialized layout.
        """
        if not isinstance(root, View):
            raise TypeError(f"layout must be a View, got {type(root).__name__}")
        for cid in self._layout_control_ids:
            self._transport.unregister(cid)
        self._layouts[name] = Layout(root, self._overlay)
        self._layout_control_ids = self.register(root)
        self._sync_overlays()
        return name

    def add_layout(self, root: View, name: str = "") -> str:
        """Register a layout (raise if *name* is already a scene or layout)."""
        if name in self._scenes or name in self._layouts:
            raise ValueError(f"Scene or layout {name!r} already exists")
        return self.set_layout(root, name)

    def register(self, root: View) -> set[str]:
        """Register handlers + inject push callbacks for *root*'s subtree.

        Returns the set of control-view ids (for unregistration on replacement).
        """
        from .views import iter_control_views, iter_log_views

        registered: set[str] = set()
        for view in iter_control_views(root):
            view.control.register_handlers(self._transport)
            view._push = self._push_control_update
            registered.add(view.id)
        for view in iter_log_views(root):
            view._push = self._push_log_update
        return registered

    def resolve_control(self, cid: str) -> Any | None:
        """Return the control with id *cid* by walking layouts and dialogs."""
        from .views import iter_control_views

        for layout in self._layouts.values():
            for view in iter_control_views(layout.base):
                if view.id == cid:
                    return view.control
        for scoped in self._overlay._dialogs.values():
            for dialog in scoped.values():
                for view in iter_control_views(dialog.content):
                    if view.id == cid:
                        return view.control
        return None

    async def dispatch_control_event(
        self, msg_type: str, payload: dict[str, Any]
    ) -> None:
        """Handle an inbound control / file-browser event."""
        from ._controls import ControlEvent, parse_table_event

        event = ControlEvent(browser_id=payload.get("browser_id"))
        if msg_type == "file_browser_navigate":
            await self._handle_file_browser_navigate(payload)
            return
        if msg_type == "file_browser_select":
            await self._handle_file_browser_select(payload, event)
            return
        if msg_type == "control:group_toggle":
            cid = payload.get("control_id")
            await self._fire(cid, "toggle", payload.get("value"), event)
            return
        if not msg_type.startswith("control:"):
            return

        event_name = msg_type[len("control:") :]
        cid = payload.get("control_id")
        ctrl = self.resolve_control(cid) if cid else None
        if ctrl is None and self._client_log is not None and cid == self._client_log.id:
            ctrl = self._client_log

        if ctrl is not None:
            d = ctrl.handle_event(event_name, payload)
            if d.push is not None:
                self._push_control_update(cid, d.push)
            if d.event is not None:
                await self._fire(cid, d.event, d.value, event)
            return

        d = parse_table_event(event_name, payload)
        if d.event is not None:
            await self._fire(cid, d.event, d.value, event)
            return
        data = None if event_name == "click" else payload.get("value")
        await self._fire(cid, event_name, data, event)

    async def _fire(
        self, cid: str | None, event_name: str, value: Any, control_event: Any
    ) -> None:
        """Look up and invoke ``(cid, event_name)`` with *value*; log on error."""
        handler = self._transport.get(cid, event_name) if cid else None
        if handler is None:
            return
        try:
            await handler(value, control_event)
        except Exception:
            import logging

            logging.getLogger(__name__).exception(
                "Error in %r handler for %r", event_name, cid
            )

    def _push_control_update(self, cid: str, value: Any) -> None:
        """Push a lightweight ``control_update`` message for one control."""
        self._transport.send(
            {"type": "control_update", "scene": "", "id": cid, "value": value}
        )

    def _push_log_update(self, view_id: str, action: str, lines: Any = None) -> None:
        """Push a lightweight ``log_update`` message for one ``LogView``."""
        message: dict[str, Any] = {
            "type": "log_update",
            "id": view_id,
            "action": action,
        }
        if lines is not None:
            message["lines"] = lines
        self._transport.send(message)

    def open_file_chooser(self, cid: str, *, path: str | None = None) -> None:
        """Open the file browser dialog for control *cid* (from the backend)."""
        ctrl = self.resolve_control(cid)
        if ctrl is None:
            return
        start = path if path is not None else (ctrl.value or ctrl.root or "")
        self._transport.send(
            {"type": "file_browser_show", "scene": "", "control_id": cid, "path": start}
        )

    def close_file_chooser(self, cid: str) -> None:
        """Close the file browser dialog for control *cid*."""
        self._transport.send({"type": "file_browser_close", "control_id": cid})

    async def _handle_file_browser_navigate(self, payload: dict[str, Any]) -> None:
        from ._file_browser import list_directory

        cid = payload.get("control_id")
        path = payload.get("path") or ""
        ctrl = self.resolve_control(cid) if cid else None
        root = getattr(ctrl, "root", None) if ctrl is not None else None
        message = list_directory(path, root=root)
        message.update({"type": "file_browser_listing", "control_id": cid})
        await self._transport.send_async(message)

    async def _handle_file_browser_select(
        self, payload: dict[str, Any], event: Any
    ) -> None:
        cid = payload.get("control_id")
        path = payload.get("path") or ""
        ctrl = self.resolve_control(cid) if cid else None
        if ctrl is not None:
            ctrl.set_value(path)
            self._push_control_update(cid, ctrl.get_value())
        handler = self._transport.get(cid) if cid else None
        if handler is not None:
            try:
                await handler(path, event)
            except Exception:
                import logging

                logging.getLogger(__name__).exception(
                    "Error in file chooser handler for %r", cid
                )

    def remove_view(self, view_id: str, *, scene: str | None = None) -> None:
        """Remove a mounted overlay view by its stable id."""
        self._overlay.remove_view(view_id, scene=scene)

    def update_view(self, view_id: str, **fields: Any) -> None: ...

    def serialize(self, *, scene: str | None = None) -> dict[str, Any] | None:
        if scene is not None:
            return self._scene_layout_for(scene)
        return self._layout_serialized_for("")

    # ── Overlay state (delegates) ───────────────────────

    @property
    def _global_overlay(self) -> list[Any]:
        return self._overlay._global_overlay

    @property
    def _scene_overlays(self) -> dict[str, list[Any]]:
        return self._overlay._scene_overlays

    @property
    def _injected_overlay_ids(self) -> set[int]:
        return self._overlay._injected_overlay_ids

    # ── Overlay sync + serialization ────────────────────

    def _reserialize_overlays(self) -> None:
        """Re-serialize the cached layouts (no push)."""
        from .views import SceneView, StackView

        if (self._global_overlay or self._scene_overlays) and not self._layouts:
            self._layouts[""] = Layout(
                StackView("vertical", [SceneView("")]), self._overlay
            )
        overlay = self._global_overlay or None
        for name, layout in self._layouts.items():
            self._inject_scene_overlays(layout.base)
            self._layouts_serialized[name] = serialize_layout(
                layout.base, name=name, overlay=overlay
            )
        for name in list(self._scene_layouts_serialized):
            root = StackView("vertical", [SceneView(name)])
            self._inject_scene_overlays(root)
            self._scene_layouts_serialized[name] = serialize_layout(root, name=name)

    def _sync_overlays(self) -> None:
        """Re-serialize the cached layouts and push the updates."""
        self._reserialize_overlays()
        self._push_layout_updates_threadsafe()

    def _inject_scene_overlays(self, root: View) -> None:
        from .views import iter_scene_views

        for scene_view in iter_scene_views(root):
            base = [
                v for v in scene_view.overlay if id(v) not in self._injected_overlay_ids
            ]
            scene_view.overlay = base + list(
                self._scene_overlays.get(scene_view.scene, [])
            )

    def _layout_serialized_for(self, layout_name: str) -> dict[str, Any] | None:
        return self._layouts_serialized.get(layout_name)

    def _scene_layout_for(self, scene_name: str) -> dict[str, Any] | None:
        from .views import SceneView, StackView

        if scene_name == "":
            if "" not in self._layouts:
                self._layouts[""] = Layout(
                    StackView("vertical", [SceneView("")]), self._overlay
                )
            if "" not in self._layouts_serialized:
                self._inject_scene_overlays(self._layouts[""].base)
                self._layouts_serialized[""] = serialize_layout(
                    self._layouts[""].base,
                    name="",
                    overlay=self._global_overlay or None,
                )
            return self._layouts_serialized.get("")

        layout = self._scene_layouts_serialized.get(scene_name)
        if layout is None:
            root = StackView("vertical", [SceneView(scene_name)])
            self._inject_scene_overlays(root)
            layout = serialize_layout(root, name=scene_name)
            self._scene_layouts_serialized[scene_name] = layout
        return layout

    async def _push_layout_updates(self) -> None:
        if self._state.server is None:
            return
        for session in self._state.server.get_browser_sessions():
            layout_name = session.get("layout")
            if layout_name is not None:
                payload = self._layout_serialized_for(layout_name)
            else:
                payload = self._scene_layout_for(session["scene"])
            if payload is not None:
                await self._state.server.push_layout_to_session(session["id"], payload)

    def _push_layout_updates_threadsafe(self) -> None:
        if self._state.server is None or self._state.loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._push_layout_updates(), self._state.loop)
