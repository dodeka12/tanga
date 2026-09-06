# Viz Client Log + Object-Attach Fix — Overview

**Created:** 2026-09-05 | **Status:** Done | **Branch:** `fix/examples`

## Goal

Two related fixes in the live viewer:

1. **Fix the broken `parent_id` attach.** A `GroupView(..., parent_id="sphere")`
   declared in a `SceneView(overlay=[...])` never appears on first load because
   the browser builds the layout (and calls `addOverlay`) before the scene
   entities arrive, and the attach path is a one-shot lookup with no retry.
2. **Add a general frontend → backend log protocol.** Frontend warnings/errors
   are sent to the backend through the *same* unified `(id, event)` envelope, and
   a backend **`ClientLog` control** (a separate class) receives them and decides
   what to do (default: `logging`). The first consumer is the attach warning that
   motivated this work.

## Architecture (short)

- **Attach fix** lives in `py/pytanga/viz/templates/views/three-view.js`:
  `addOverlay()` defers `parent_id` groups whose parent mesh is not yet in
  `sceneObjects`, and `_upsertObject()` drains the deferred queue once the parent
  entity is registered.
- **Log protocol** reuses the existing event path end-to-end:
  - frontend `sendEvent(CLIENT_LOG_ID, "log", { level, message, source, data })`
  - server maps `event:"log"` → `control:log` and routes it to the control
    dispatch core
  - `LayoutHost.dispatch_control_event` resolves the reserved id to a
    `ClientLog` control, whose `handle_event` normalizes the payload into a
    `ClientLogRecord` and fires the `("client_log", "log")` handler (the sink).

## Canonical contract (fixed up front)

### Wire message (client → server)

```json
{
  "type": "event",
  "target": "client_log",
  "event": "log",
  "data": { "level": "warn", "message": "…", "source": "three-view.js", "data": {} }
}
```

- `target` is the reserved constant `CLIENT_LOG_ID = "client_log"`.
- `event` is always `"log"`; severity is carried in `data.level`.
- `level` ∈ `"debug" | "info" | "warn" | "error"` (anything else is treated as
  `"warn"` on the backend).
- `message` is a required string; `source` and `data` are optional.

### Frontend helper (`events.js`)

```js
export const CLIENT_LOG_ID = 'client_log';
export function sendLog(level, message, { source = null, data = null } = {}) {
    sendEvent(CLIENT_LOG_ID, 'log', { level, message, source, data });
}
```

### Backend control (`_controls.py`)

```python
CLIENT_LOG_ID = "client_log"

@dataclass
class ClientLogRecord:
    level: str
    message: str
    source: str | None = None
    data: dict[str, Any] | None = None
    browser_id: str | None = None

@dataclass
class ClientLog(Control):          # id passed positionally, == CLIENT_LOG_ID
    kind: str = "client_log"
    on_log: Handler = _default_client_log_sink
    # handle_event("log", payload) -> Dispatch("log", ClientLogRecord(...))
```

- `ClientLog` is backend-only: never serialized, never placed in a layout.
- `handle_event("log", payload)` parses `level/message/source/data/browser_id`
  and returns `Dispatch("log", record)`; the inherited `register_handlers` maps
  `on_log` → `("client_log", "log")`.
- `_default_client_log_sink(record, event)` logs via
  `logging.getLogger("tanga.viz.client")` with the level mapping below.

### Level mapping (backend)

| `data.level` | Python logging call |
|---|---|
| `debug` | `logger.debug` |
| `info` | `logger.info` |
| `warn` | `logger.warning` |
| `error` | `logger.error` |
| other | `logger.warning` |

## Decisions (confirmed)

- Logs go through the **unified event envelope** (`sendEvent`), not a new
  `client_log` WS message type.
- One reserved control id (`"client_log"`) and one event name (`"log"`) — level
  is data, not the event name — so the `_EVENT_MSG_MAP` gets a single entry and
  the sink is a single `(id, "log")` handler.
- `ClientLog` is a `Control` subclass (a separate class), living in
  `_controls.py` alongside the other controls; it is made resolvable by a small
  `LayoutHost` hook, not by being placed in a layout.
- The deferred-attach fix is frontend-only; the server's `view_layout`-before-
  `scene_update` ordering is intentional and stays.
- Default sink is `logging.getLogger("tanga.viz.client")`; the user can replace
  it via `viz.on_client_log(handler)`.
- **Trace forwarding** (the frontend `_log(...)` init/WS lines) is opt-in:
  - **A** (default) — only `console.warn`/`console.error` are forwarded
    (Phases 3–4).
  - **B** — trace/init lines are also forwarded at `info` level.
  - **C** — B is gated behind `setLogForwarding(true)` (or the `?log=1` URL
    parameter), so trace noise is off unless explicitly enabled.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-client-log-control.md](./01-client-log-control.md) | Backend `ClientLogRecord` + `ClientLog(Control)` model + unit tests |
| 2 | [02-log-event-routing.md](./02-log-event-routing.md) | Wire `event:"log"` → `control:log` → `ClientLog` dispatch + `viz.on_client_log` |
| 3 | [03-frontend-send-log.md](./03-frontend-send-log.md) | `events.js` `CLIENT_LOG_ID` + `sendLog()` + JS test |
| 4 | [04-frontend-log-migration.md](./04-frontend-log-migration.md) | Route existing `console.warn/error` sites through `sendLog` |
| 5 | [05-frontend-trace-forwarding.md](./05-frontend-trace-forwarding.md) | Opt-in `setLogForwarding`/`?log=1` trace/init forwarding |
| 6 | [06-deferred-attach.md](./06-deferred-attach.md) | Deferred `parent_id` attach fix in `three-view.js` |
| 7 | [07-docs-changelog.md](./07-docs-changelog.md) | Docs + changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz -q` (phases 1–2, 6).
- **JS unit:** `node --test 'dev/src/js-tests/*.test.mjs'` (phases 3–6).
- **JS syntax:** `node --check <changed-file>` for edited templates.
- **Docs:** `uv run mkdocs build --strict` (phase 6).

## Non-goals

- No change to the server's `view_layout`-before-`scene_update` push order.
- No wiring of the **SDF viewer** (`sdf/sdf_viewer.js`) into `sendLog` — it is a
  separate frontend and a follow-up.
- No client-side rate-limiting/dedup of log events (the current `console.*`
  sites are not in per-frame hot paths).
- No serialization of `ClientLog` to the frontend; it is backend-only.
