# Image load events & LOD toggle fix — Overview

**Created:** 2026-10-23 | **Status:** Done | **Branch:** `fix/image-loading`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` — the
> "Image canvas (extension recipe)" and "Image background" sections — and
> `docs/dev/architecture/viz-controls-and-interactions.md` — the "Client →
> server logging" and "Adding a new control kind" sections).  This work adds a
> backend-only reserved control (`image_status`) that **mirrors the existing
> `client_log` pattern** (no new architecture seam), but the developer docs must
> still be updated in Phase 5.

## Goal

1. **Fix the LOD toggle.** A tiled pyramid image must not flip between two
   resolution levels when the view sits on a power-of-two level boundary —
   today `updateImageLod` re-resolves the level every animation frame with no
   hysteresis, so sub-ULP camera/zoom jitter ping-pongs two levels.
2. **Add image lifecycle events.** Three frontend→backend events —
   `image_loaded` (an image's first texture is displayable), `image_tile_load`
   (the frontend starts fetching a new pyramid level), `image_tile_loaded` (that
   level's texture was swapped in) — so an app can drive "loading…" vs "ready"
   UI (e.g. `show_banner`).

## Architecture (short)

- **LOD** lives in the shared pure helper `renderers/image-tiles.js`
  (`levelForScreen`) and is driven every frame by `updateImageLod` in
  `renderers/image.js` (shared by the scene `image` entity and the
  `background_image` quad via `image-background.js`).
- **Events** reuse the unified client→server envelope in `templates/events.js`
  (`sendEvent`) and the backend-only reserved-control pattern already used by
  `client_log`: a reserved id + a `Control` subclass whose `handle_event`
  normalizes the payload into a record and fires the `(id, event)` handler.

## Fixed contract (decided up front)

### `levelForScreen` hysteresis (image-tiles.js)

Add an optional `currentLevel` argument; when it is an integer the result is
clamped by a ±2% dead-band around the boundary so a level change needs a clear
crossing:

```js
const _HYSTERESIS = 0.02;

function _levelResolution(pyramid, level) {
    return Math.max(
        Math.ceil(pyramid.width / (2 ** level)),
        Math.ceil(pyramid.height / (2 ** level)),
    );
}

export function levelForScreen(pyramid, screenLongSide, currentLevel) {
    const levels = pyramid.levels || 1;
    if (!(Number.isFinite(screenLongSide) && screenLongSide > 0)) return 0;
    // Ideal level (no hysteresis): coarsest level whose long side >= screen size.
    let ideal = 0;
    while (ideal + 1 < levels) {
        if (_levelResolution(pyramid, ideal + 1) < screenLongSide) break;
        ideal++;
    }
    if (!Number.isInteger(currentLevel)) return ideal;
    if (ideal === currentLevel) return ideal;
    if (ideal < currentLevel) {
        // Finer: only once the screen clearly exceeds the current level's resolution.
        const bound = _levelResolution(pyramid, currentLevel) * (1 + _HYSTERESIS);
        return screenLongSide > bound ? ideal : currentLevel;
    }
    // Coarser: only once the screen clearly falls below the new level's resolution.
    const bound = _levelResolution(pyramid, ideal) * (1 - _HYSTERESIS);
    return screenLongSide < bound ? ideal : currentLevel;
}
```

### `updateImageLod` generation token (image.js)

Per-layer state gains two fields (they default to `undefined`/`0`, so the
`_tiledLayers.push({ img, index, level })` sites are unchanged):
`pendingLevel` (level being fetched) and `generation` (monotonic counter).  A
fetch is started with a captured `generation`; on completion it swaps **only if
`layer.generation` still equals the captured value**.  Cancelling an in-flight
fetch also bumps `generation`, so a stale fetch can never overwrite a newer one.

### Image event contract

- Reserved id: `IMAGE_STATUS_ID = "image_status"` (frontend `events.js`, backend
  `_controls.py`; **backend-only**, never serialized).
- Frontend helper `sendImageEvent(event, data)` → `sendEvent("image_status",
  event, data)` → wire `{ type:"event", target:"image_status", event, data }`.
- Server `_EVENT_MSG_MAP`: `"image_loaded" → "control:image_loaded"`,
  `"image_tile_load" → "control:image_tile_load"`,
  `"image_tile_loaded" → "control:image_tile_loaded"`.
- Payloads (JSON, all from the frontend; `browser_id` is injected by `server.py`):

  | event | payload |
  |---|---|
  | `image_loaded` | `{ image_id, source, width, height }` (no `level`) |
  | `image_tile_load` | `{ image_id, source:"tiled", width, height, level, tile_version }` |
  | `image_tile_loaded` | `{ image_id, source:"tiled", width, height, level, tile_version }` |

- Backend `ImageStatusRecord(image_id, source=None, width=None, height=None,
  level=None, tile_version=None, browser_id=None)`.
- Backend `ImageStatus(Control)` with `on_image_loaded` / `on_image_tile_load` /
  `on_image_tile_loaded` (all `ControlHandler`, default no-op).  `handle_event`
  parses the payload and returns `Dispatch(event, record)`.
- Public API (Visualizer): `viz.on_image_loaded(h)`, `viz.on_image_tile_load(h)`,
  `viz.on_image_tile_loaded(h)`, each `async def h(record, event)`.

## Decisions (confirmed)

- **Three separate events** — `image_loaded`, `image_tile_load`,
  `image_tile_loaded` (not one `image` event with a `phase` field).
- **Reserved backend-only control** `image_status`, mirroring `client_log`
  (not a layout-placed control; not serialized; not exported from `__init__.py`).
- **`image_loaded` = first displayable texture** (spinner-off).  Subsequent
  pyramid zoom changes report through `image_tile_load` / `image_tile_loaded`.
- **2% hysteresis** is the dead-band width; no time-based debounce (hysteresis +
  generation token is sufficient to kill the toggle).
- **Frontend `sendImageEvent` stub** is added to the export bootstrap so the
  bundled renderers (which call it with the import stripped) stay valid in
  offline/export HTML.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-frontend-lod-hysteresis.md](./01-frontend-lod-hysteresis.md) | Hysteresis in `levelForScreen` + generation token in `updateImageLod` |
| 2 | [02-backend-image-status-control.md](./02-backend-image-status-control.md) | `IMAGE_STATUS_ID` + `ImageStatusRecord` + `ImageStatus(Control)` |
| 3 | [03-server-routing-and-api.md](./03-server-routing-and-api.md) | `_EVENT_MSG_MAP` + `LayoutHost` resolution + `Visualizer.on_image_*` |
| 4 | [04-frontend-emit-events.md](./04-frontend-emit-events.md) | `sendImageEvent` + emit points + bundle rebuild |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Developer docs + example + branch changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q` — Python regression.
- `uv run ruff check .` and `uv run ty check` — lint + type gates.
- `node js/dev/tests/check-syntax.mjs` — frontend syntax gate.
- `node --test js/dev/tests/*.test.mjs` — JS unit tests (incl. hysteresis).
- `uv run python tools/build-viewer-js.py` — rebuild the committed viewer bundle after template/`_bootstrap` edits.
- `uv run python tools/generate-example-docs.py` — example docs (Phase 5).
- `uv run mkdocs build --strict` — docs gate (Phase 5).

## Non-goals

- No time-based debounce/throttle in `_updateImageLod` (hysteresis is the fix).
- No per-tile events (only per-level `image_tile_load` / `image_tile_loaded`).
- No new wire message type — reuses the existing `{type:"event", …}` envelope.
- No change to `ImagePyramid` tile encoding/geometry or the tile HTTP route.
- No raising `MAX_IMAGE_LAYERS`; no merge of the scene mesh and background quad.
