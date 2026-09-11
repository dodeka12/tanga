# Phase 4 — Route existing frontend warnings/errors through `sendLog`

## Goal

Prove the log channel works by migrating the live viewer's existing
`console.warn` / `console.error` sites to *also* call `sendLog` (keeping the
DevTools `console.*` output). Excludes `three-view.js` line 151, which Phase 5
rewrites.

## Files

- Edit: `py/pytanga/viz/templates/viewer.js`
- Edit: `py/pytanga/viz/templates/scene-builder.js`
- Edit: `py/pytanga/viz/templates/renderers/factory.js`
- Edit: `py/pytanga/viz/templates/renderers/utils.js`
- Edit: `py/pytanga/viz/templates/views/banner-view.js`
- Edit: `py/pytanga/viz/templates/controls-panel.js`

## Steps

- [x] **4.1 — Import `sendLog` where used**
  - Add `sendLog` to the existing `events.js` import in each edited module
    (some modules import from `events.js` already; add the import otherwise).

- [x] **4.2 — Migrate each site (keep `console.*`)**
  - `viewer.js:229` — WS message parse failure → `sendLog('error', …, { source: 'viewer.js' })`.
  - `renderers/factory.js:157` — unknown entity kind → `sendLog('warn', …, { source: 'factory.js' })`.
  - `renderers/utils.js:689` — texture-label render failure → `sendLog('warn', …, { source: 'utils.js' })`.
  - `scene-builder.js:83`, `banner-view.js:77`, `controls-panel.js:389` — KaTeX
    failures → `sendLog('warn', …, { source: '<file>' })`.

- [x] **4.3 — `three-view.js:195` (WebGL fallback)**
  - WebGL renderer creation failure → `sendLog('error', …, { source: 'three-view.js' })`
    alongside the existing warning/banner.

## Validation

`node --test 'dev/src/js-tests/*.test.mjs' && node --check py/pytanga/viz/templates/viewer.js`

## Notes

- Do **not** touch `three-view.js:151` here — Phase 5 changes that warning into
  a deferral and reports it through `sendLog` itself.
- `sendLog` no-ops when the socket is closed, so these additions are safe during
  startup/reconnect.
