# Viz Banner / Dialog Overlay — Overview

**Created:** 2026-08-26 | **Status:** Planned | **Branch:** `feat/small-extensions`

## Goal

Add a first-class **banner/dialog** system to the viewer:

- a banner with markdown/KaTeX text the user can acknowledge;
- a banner offering a set of custom options (buttons, sliders, dropdowns — any
  control usable in a `ControlGroup`);
- a convenience **yes/no/cancel** banner;
- a **non-dismissable (modal)** banner for "calculating…" states (dimmed
  backdrop, blocks the scene, no close/click-away);
- fractional alignment `(align_x, align_y) ∈ [0,1]²`;
- backend-removable (`remove_banner` / `clear_banners`);
- **global** (full-screen) and **per-scene** (inside a scene pane) variants;
- backend-registered handlers for the banner's controls, plus an optional
  `on_close` notification;
- `auto_hide` (default `True`) — the banner removes itself once an option is
  selected; otherwise the backend must remove it;
- **handler-driven** — a control/interaction handler can show a banner, ensure
  it is visible (`await show_banner_async(...)`), and fire-and-forget an
  expensive computation onto the **user loop** (or an executor for sync
  scripts) with a one-shot `done` callback that cleans up — without stalling
  the visualization loop — seamless in `VisualizerApp`.

Banners follow the existing **frontend `View` base class** architecture: a
full-screen `OverlayView` container holds `BannerView` instances (both extend
`View`), so banners compose with the rest of the view system.

## Architecture (short)

- **Two-layer mirror.** Python `Banner` dataclass + serializer in
  `py/pytanga/viz/_banner.py`; JS `OverlayView` / `BannerView` in
  `templates/views/`.
- **Dynamic, not static.** Banners are add/remove-able at runtime, so they use
  dedicated messages (`banner_define` / `banner_remove` / `banner_clear`)
  rather than the static `view_layout` tree.
- **Buttons = ordinary controls.** A banner's options are regular `Control`
  objects (slider/dropdown/button) serialized by the same
  `_serialize_one_control`; their handlers go into the existing
  `_handler_registry`, so the existing `control:change` / `control:click`
  dispatch just works. `on_close` is registered under a reserved
  `__banner__<scope>/<id>` key and dispatched by a new `banner_closed` message.
- **Reuse rendering + math.** `BannerView` reuses `controls-panel.js`
  `createSlider` / `createButton` / `createDropdown` and the `marked` +
  `renderMathInElement` KaTeX pipeline used by annotations.
- **Two-loop handoff.** Handlers run on the server loop (`self._loop`). In a
  `VisualizerApp` the user's own loop (running `_app_main`) is captured, and a
  handler hands blocking work to it fire-and-forget via
  `run_coroutine_threadsafe` (optionally with a one-shot `done` callback),
  keeping the server loop responsive. For plain sync `Visualizer` scripts,
  `run_blocking(...)` uses an executor instead.

## Wire contract (fixed up front; both sides implement against this)

### `banner_define` (server → client)

```json
{
  "type": "banner_define",
  "scene": null,
  "id": "banner_1",
  "title": "",
  "text": "## Calculating…\n\n$e^{i\\pi} = -1$",
  "align_x": 0.5,
  "align_y": 0.5,
  "auto_hide": true,
  "dismissable": true,
  "controls": [
    { "id": "banner_1_ok", "kind": "button", "label": "OK" }
  ]
}
```

- `scene` is `null` for a **global** banner, or a scene name (`""` = main
  scene) for a **per-scene** banner.
- `controls` reuse the existing control-def shape (`kind`, `label`, plus
  `min`/`max`/`step`/`default` for sliders and `options`/`default` for
  dropdowns). `[]`/absent = informational banner (no buttons).
- `align_x` / `align_y` in `[0, 1]`: `(0,0)` → banner's top-left at the
  container's top-left; `(1,1)` → banner's bottom-right at the container's
  bottom-right; `(0.5,0.5)` → centered. The container is the **viewport** for
  global banners and the **scene pane** for per-scene banners.
- `dismissable=false` → **modal**: full-screen (or full-pane) dimmed backdrop,
  no ✕, no click-away, blocks interaction.
- `auto_hide=true` → banner removes itself on any control interaction.

### `banner_remove` / `banner_clear` (server → client)

```json
{ "type": "banner_remove", "scene": null, "id": "banner_1" }
{ "type": "banner_clear", "scene": null }
```

### `banner_closed` (client → server)

```json
{ "type": "banner_closed", "id": "banner_1", "browser_id": "…" }
```

Sent only when the user dismisses a `dismissable` banner (✕ / click-away).
Routes through the existing control callback and invokes `on_close`.

## Decisions (confirmed)

- `dismissable=false` → **modal** (dimmed backdrop, blocks scene), per request.
- Banners support **global** and **per-scene** scope (`scene_name=None` vs a
  scene name); the scene handle exposes scoped `show_banner` / `remove_banner`
  / `clear_banners`.
- Backend state lives on `Visualizer` (`self._banners`), not on `Scene`
  (global banners have no scene). Button handlers still share the global
  `_handler_registry` (consistent with group controls).
- Existing ad-hoc internal warning banners (SDF/WebGL, version mismatch) are
  **not** migrated in this pass.
- **Handler-friendly + offload.** `show_banner_async` / `remove_banner_async` /
  `clear_banners_async` are loop-safe (like `flush_async`), and `VisualizerApp`
  gains `submit_user(..., done=...)` / `run_user` / `run_user_sync` (plus
  `Visualizer.run_blocking`) so handlers can fire-and-forget compute off the
  server loop and clean up in a one-shot completion callback.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-banner-model.md](./01-python-banner-model.md) | `Banner` dataclass, `serialize_control_defs`, `serialize_banner` (+ tests) |
| 2 | [02-visualizer-banner-api.md](./02-visualizer-banner-api.md) | `show_banner`/`alert`/`confirm`/`remove_banner`/`clear_banners` + loop-safe `*_async` variants, handler + `on_close` registration, `banner_closed` dispatch, `VizSceneHandle` scoped API (+ tests) |
| 3 | [03-user-loop-offload.md](./03-user-loop-offload.md) | `VisualizerApp` user-loop capture + `submit_user`/`run_user`/`run_user_sync`, `Visualizer.run_blocking` — offload compute off the server loop (+ tests) |
| 4 | [04-frontend-overlay-banner-view.md](./04-frontend-overlay-banner-view.md) | JS `OverlayView` + `BannerView` (KaTeX text, control factories, align anchor, auto-hide, modal backdrop) + smoke |
| 5 | [05-frontend-routing.md](./05-frontend-routing.md) | `banner.js` manager, `viewer.js` global-vs-scene routing, `ThreeJsView` per-scene banners, `viewer.html` include |
| 6 | [06-docs-example-changelog.md](./06-docs-example-changelog.md) | Slider `on_press`/`on_release` events, examples (`banner_types.py`, `heavy_work.py`), docs page + nav, changelog, full validation |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/ -q` (new `test_banner.py` + existing).
- **JS (DOM modules):** browser smoke pages under `dev/src/js-tests/` per phase
  (mirroring `control-group-view-smoke.html`); plus `node --check` on new
  modules.
- Every phase ends with a runnable validation command before the next starts.

## Non-goals

- Migrating the existing internal warning banners (SDF/WebGL, version mismatch).
- Drag-to-reposition banners (fixed `align_x`/`align_y` only).
- Persisting banner state across reconnects.
