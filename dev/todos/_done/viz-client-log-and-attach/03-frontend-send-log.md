# Phase 3 — Frontend `sendLog` helper

## Goal

Expose `CLIENT_LOG_ID` + `sendLog(level, message, { source, data })` in
`events.js`, the client half of the log contract.

## Files

- Edit: `py/pytanga/viz/templates/events.js`
- Edit: `dev/src/js-tests/events.test.mjs`

## Steps

- [x] **3.1 — `events.js`**
  - Add `export const CLIENT_LOG_ID = 'client_log';`.
  - Add `export function sendLog(level, message, { source = null, data = null } = {})`
    that calls `sendEvent(CLIENT_LOG_ID, 'log', { level, message, source, data })`.
  - Extend the module header comment to mention the log channel.

- [x] **3.2 — JS test (`events.test.mjs`)**
  - `sendLog("warn", "msg", { source: "x" })` emits
    `{ type: 'event', target: 'client_log', event: 'log',
       data: { level: 'warn', message: 'msg', source: 'x', data: null } }`.
  - `sendLog` no-ops when the socket is closed (mirror the existing
    `sendEvent` closed-socket test).

## Validation

`node --test dev/src/js-tests/events.test.mjs`

## Notes

- `sendEvent` already guards on `_ws.readyState === WebSocket.OPEN`, so
  `sendLog` needs no socket check of its own.
