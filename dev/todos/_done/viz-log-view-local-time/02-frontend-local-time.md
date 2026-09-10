# Phase 2 — `MessageView` local-time formatting

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Render the first column in the browser's local timezone, honoring the
`show_date` / `show_utc_offset` flags, and wire the flags through `build.js`.

## Files

- Edit: `py/pytanga/viz/templates/views/message-view.js`
- Edit: `py/pytanga/viz/templates/views/build.js`
- Edit: `dev/src/js-tests/message-view.test.mjs`

## Steps

- [x] **2.1 — Accept the flags in `MessageView`**
  - Add `show_date = false` and `show_utc_offset = false` to the constructor
    destructuring; store `this.showDate` / `this.showUtcOffset`.
- [x] **2.2 — Add `_timeOf(line)` (local conversion)**
  - Parse `line.time` as `YYYY-MM-DDTHH:MM:SS[.ffffff][Z|±HH:MM]`; fall back to
    the raw string for non-ISO values.
  - Convert the wall-clock components to the browser's local timezone via
    `Date.UTC(...)` + `new Date(...)` + `getHours`/`getMinutes`/`getSeconds`,
    preserving the microsecond fraction by re-appending it (JS `Date` is
    millisecond-only).  Honor any stored offset (default UTC).
  - Return space-separated parts: `[date] HH:MM:SS[.ffffff] [offset]` per the
    flags; the local offset is `±HH:MM` from `-d.getTimezoneOffset()`.
- [x] **2.3 — Use `_timeOf` in `_appendRow`**
  - Replace the `String(line.time)` cell fill with `this._timeOf(line)`.
- [x] **2.4 — Wire flags in `build.js`**
  - In the `log_view` branch, pass `show_date: node.show_date ?? false` and
    `show_utc_offset: node.show_utc_offset ?? false` to `MessageView`.
- [x] **2.5 — JS tests**
  - Add `_timeOf` tests: default (time only), `show_date`, `show_utc_offset`,
    both, a no-microseconds value, and a non-ISO fallback.
  - Compute the expected local offset dynamically from
    `new Date().getTimezoneOffset()` (do not hardcode a zone), so the test is
    TZ-independent.

## Validation

`node --check py/pytanga/viz/templates/views/message-view.js py/pytanga/viz/templates/views/build.js && node --test 'dev/src/js-tests/*.test.mjs'`

## Notes

- `message-view.js` is the renamed `log-view.js`; `MessageView` is registered
  via `registerMessageView`/`applyMessageUpdate` (unchanged).