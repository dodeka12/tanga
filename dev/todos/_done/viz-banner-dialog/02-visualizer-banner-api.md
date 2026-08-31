# Phase 2 — `Visualizer` banner API + handler dispatch

## Goal

Expose banner lifecycle on `Visualizer` (and `VizSceneHandle`), wire the
buttons into the existing control registry, and dispatch `banner_closed` to an
`on_close` handler.

## Steps

- [x] **2.1 — State**
  - `self._banners: dict[str | None, dict[str, Banner]]` on
    `Visualizer.__init__` (global banners under `None`), plus a counter for
    auto-generated ids.
  - Register `on_close` in a dedicated `self._banner_close_handlers` dict keyed
    by banner id (ids are unique across scopes), so the `banner_closed` message
    (which carries only the id) can be dispatched.

- [x] **2.2 — `show_banner(...) -> str`**
  - Signature: `show_banner(text, *, id=None, title="", align_x=0.5,
    align_y=0.5, auto_hide=True, dismissable=True, controls=None,
    on_close=None, scene_name=None)`.
  - Auto-generate a unique `id` when omitted; register each control's
    `on_change` / `on_click` into `_handler_registry` (remember them so
    `remove_banner` can unregister).
  - Store the `Banner`, push `banner_define`.

- [x] **2.3 — Conveniences**
  - `alert(text, *, title="", ok_label="OK", on_ok=None, ...)` → single-button
    acknowledge banner (returns banner id).
  - `confirm(text, *, title="", yes_label="Yes", no_label="No",
    cancel_label="Cancel", on_yes=None, on_no=None, on_cancel=None, ...)` →
    three-button banner.

- [x] **2.4 — Removal**
  - `remove_banner(banner_id, *, scene_name=None)` → unregister handlers, pop
    state, push `banner_remove`.
  - `clear_banners(scene_name=None)` → unregister all in scope, clear, push
    `banner_clear`.

- [x] **2.5 — `_push_banner*` helpers**
  - `_push_banner(banner, scene_name)`, `_push_banner_remove(id, scene_name)`,
    `_push_banner_clear(scene_name)` using
    `run_coroutine_threadsafe(self._server.push_raw(...), self._loop)` (mirror
    `_push_controls`).

- [x] **2.6 — Awaitable banner push (loop-safe)**
  - Extract the loop-detection from `flush_async` into
    `async def _on_server_loop(self, coro_factory)` (await inline when running
    on `self._loop`, else `run_coroutine_threadsafe` + `asyncio.wrap_future`).
  - Add `_push_banner_async(banner, scene_name)` /
    `_push_banner_remove_async(id, scene_name)` /
    `_push_banner_clear_async(scene_name)` (must run on `self._loop`).
  - Public `show_banner_async(...)` / `remove_banner_async(...)` /
    `clear_banners_async(...)` — same signatures as the sync forms but
    awaitable, built on `_on_server_loop` so they work seamlessly from a
    handler (on `self._loop`) **and** from `init()` / `cleanup()` (user loop).
    A handler awaits this to guarantee the banner is visible before it blocks
    or offloads work.

- [x] **2.7 — `banner_closed` dispatch**
  - `server.py`: add `"banner_closed"` to the control-message tuple so it
    reaches `_control_callback`.
  - `visualizer.py::_dispatch_control_event`: branch on
    `msg_type == "banner_closed"` → look up `self._banner_close_handlers[id]`
    and `await handler(id, event)`.

- [x] **2.8 — `VizSceneHandle` scoped API**
  - `show_banner(...)` (no `scene_name`; uses `self._name`), `remove_banner`,
    `clear_banners` delegating to `self._viz`, plus the `*_async` variants.

- [x] **2.9 — Tests (`test_banner.py`)**
  - `show_banner` stores + registers + pushes (monkeypatch `_push_banner` or
    `_server.push_raw`).
  - Auto-id uniqueness; explicit id reuse.
  - `remove_banner` / `clear_banners` unregister handlers and push removal.
  - `alert` / `confirm` produce 1 / 3 button controls with correct handlers.
  - `_dispatch_control_event("banner_closed", {"id": ...})` invokes `on_close`.
  - `VizSceneHandle.show_banner` scopes to `self._name`.
  - `show_banner_async` awaits the push on the server loop, and cross-loop
    schedules + awaits without deadlock.

## Validation

`uv run pytest py/tests/viz/test_banner.py py/tests/viz/test_controls.py -q`
