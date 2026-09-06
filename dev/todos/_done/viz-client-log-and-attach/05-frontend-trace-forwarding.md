# Phase 5 — Frontend trace/init log forwarding (opt-in)

## Goal

Add an opt-in channel that forwards the frontend's `_log(...)` init/WS trace
lines to the backend log, controlled by a flag that defaults to **off**. This
realizes the three options discussed:

- **A (default)** — only `console.warn`/`console.error` are forwarded (Phases
  3–4).
- **B** — trace/init lines are also forwarded at `info` level.
- **C** — the forwarding is gated by a flag (`setLogForwarding(true)` or
  `?log=1`), so B is opt-in.

## Files

- Edit: `py/pytanga/viz/templates/events.js`
- Edit: `py/pytanga/viz/templates/viewer.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`
- Edit: `dev/src/js-tests/events.test.mjs`

## Steps

- [x] **5.1 — `events.js` forwarding flag**
  - Add module state `let _logForwarding = false;`.
  - Export `setLogForwarding(enabled)` and `logForwardingEnabled()`.

- [x] **5.2 — `viewer.js` `_log()` forwards when enabled**
  - Import `sendLog`, `logForwardingEnabled` from `events.js`.
  - In `_log(phase, detail)`, after the existing `console.log(...)`, add
    `if (logForwardingEnabled()) sendLog('info', detail, { source: 'viewer.js', data: { phase } });`.
  - Auto-enable via the `?log=1` query parameter at bootstrap (read
    `URLSearchParams` alongside the existing `view`/`viewer` reads).

- [x] **5.3 — `three-view.js` `_log()` forwards when enabled**
  - Same pattern in `ThreeJsView._log(phase, detail)` with `source:
    'three-view.js'`.

- [x] **5.4 — JS test for the flag**
  - In `events.test.mjs`: `setLogForwarding` toggles `logForwardingEnabled()`
    (default `false`). (The gating itself is exercised by the `_log` call sites;
    keep this a unit test of the flag API.)

## Validation

`node --test dev/src/js-tests/events.test.mjs && node --check py/pytanga/viz/templates/viewer.js && node --check py/pytanga/viz/templates/views/three-view.js`

## Notes

- Default off == option A; `setLogForwarding(true)` (or `?log=1`) == option B.
- Backend side: these arrive as `info`-level `ClientLogRecord`s → the
  `tanga.viz.client` logger at `INFO`; the host process must have logging
  configured at `INFO` to see them on stdout (Python's default shows `WARNING+`).
- A Python-facing toggle (server→client message) is intentionally **not** part of
  this phase — the flag is frontend-side (`?log=1` / `setLogForwarding`).
