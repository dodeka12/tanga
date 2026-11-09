# Phase 3 — Global tooltips switch

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

`Visualizer.set_tooltips_enabled(bool)` suppresses every framework tooltip on
all connected browsers, and every newly connected browser starts with the
current setting — no per-view bookkeeping in the app.

## Files

- Edit: `py/pytanga/viz/_hosts.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/server.py`
- Edit: `py/pytanga/viz/templates/viewer.js`
- Edit: `py/tests/viz/test_layout_api.py`
- Edit: `py/tests/viz/test_server_layout.py`

## Steps

- [x] **3.1 — `UIOptionsHost` (`_hosts.py`)**
  - `class UIOptionsHost(OverlayHost)` next to `ThemeHost`, with:
    - `__init__(self, transport, layout, tooltips_enabled: bool = True)`
    - `tooltips_enabled` property
    - `serialize() -> dict` → `{"tooltips_enabled": self._tooltips_enabled}`
    - `set_tooltips_enabled(enabled: bool) -> None` → store, then
      `self._push_message({"type": "ui_options", **self.serialize()})`
  - Module docstring note: page-level UI options (currently the tooltip switch).

- [x] **3.2 — `Visualizer` wiring (`visualizer.py`)**
  - Construct `self._ui_options_host = UIOptionsHost(self._transport,
    self._layout)` next to `self._theme_host` (line ~262).
  - Public API: `tooltips_enabled` property, `set_tooltips_enabled(enabled)`
    (delegates to the host), placed next to `set_control_enabled`. No async twin
    is needed (`_transport.send` is thread-safe; unlike `set_theme` this does no
    I/O).
  - Pass `ui_options_callback=self._ui_options_host.serialize` into
    `self._server.start(...)` next to `theme_callback=`.

- [x] **3.3 — server (`server.py`)**
  - Accept `ui_options_callback: UICallback | None = None` in `VizServer.start`
    (mirror the `theme_callback` plumbing: attribute default in `__init__`,
    parameter + assignment in `start`).
  - In `_push_full_state`, immediately after the `clear_all` payload (before the
    background frames / `view_layout`), send
    `{"type": "ui_options", **self._ui_options_callback()}` when the callback is
    set (log with the same `WS SEND` shape).

- [x] **3.4 — frontend (`templates/viewer.js`)**
  - Import `setTooltipsEnabled` from `./controls-panel.js`.
  - Add a message branch: `if (msg.type === 'ui_options') {
    setTooltipsEnabled(!!msg.tooltips_enabled); return; }`.

- [x] **3.5 — Tests**
  - `test_server_layout.py`: `_server()` sets
    `server._ui_options_callback = lambda: {"tooltips_enabled": False}`; update
    `test_layout_push_orders_messages` / `test_single_scene_push` for the new
    message and add a case asserting `ui_options` comes **before**
    `view_layout` and carries `tooltips_enabled`.
  - `test_layout_api.py`: `viz.set_tooltips_enabled(False)` flips
    `viz.tooltips_enabled` and broadcasts
    `{"type": "ui_options", "tooltips_enabled": False}`. No diffing: a repeated
    identical call pushes again (matches `set_control_enabled`), so assert two
    identical messages after two calls.

## Validation

```bash
uv run pytest py/tests/viz/test_layout_api.py py/tests/viz/test_server_layout.py -q && node js/dev/tests/check-syntax.mjs
```

## Notes

- `sdf/sdf_viewer.js` has no control/view rendering and no `control_state`
  handling, so it does not need the `ui_options` branch.
- The flag is per server (not per layout/scene); it is re-sent on every
  reconnect via `_push_full_state`.
