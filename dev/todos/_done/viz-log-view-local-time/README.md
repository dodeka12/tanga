# LogView local-time formatting — Overview

**Created:** 2026-09-09 | **Status:** Done | **Branch:** `fix/misc`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make the `LogView` first column (the timestamp) configurable.  Today the
frontend shows the full stored UTC ISO-8601 string
(`YYYY-MM-DDTHH:MM:SS.ffffff+00:00`).  Change it so that, by default, only the
local wall-clock time with microseconds is shown (`HH:MM:SS.ffffff`), with the
date and the local UTC offset available as opt-in flags.

## Architecture (short)

- `LogView` (backend, `py/pytanga/viz/views.py`) keeps storing each line's
  `time` as a UTC ISO-8601 string — unchanged.
- Two new keyword-only flags on `LogView` control display:
  - `show_date: bool = False` — prepend the local `YYYY-MM-DD`.
  - `show_utc_offset: bool = False` — append the local offset to UTC `±HH:MM`.
- Both flags serialize into the `log_view` node and flow to the frontend
  `MessageView`, which converts `line.time` from UTC to the browser's local
  timezone (preserving the microsecond fraction) and assembles the column text.

### Fixed contract

- `LogView.__init__(..., show_date=False, show_utc_offset=False)`.
- `_serialize()` emits `"show_date"` and `"show_utc_offset"` booleans.
- Frontend `MessageView` constructor accepts `show_date = false`,
  `show_utc_offset = false`; `build.js` passes `node.show_date ?? false` and
  `node.show_utc_offset ?? false`.
- `_timeOf(line)` parses `line.time` (`YYYY-MM-DDTHH:MM:SS[.ffffff][Z|±HH:MM]`),
  converts to local time via `Date.UTC(...)` + `new Date(...)` (honoring any
  stored offset, defaulting to UTC), and returns space-separated parts:
  `[date] HH:MM:SS[.ffffff] [offset]` per the flags.  Non-ISO strings fall
  through unchanged.

## Decisions (confirmed)

- **Local time + local offset** — the timestamp is converted to the browser's
  local timezone, and `show_utc_offset` shows the *local* offset to UTC (e.g.
  `+02:00`), not the stored `+00:00`.
- **Microseconds preserved** — the sub-second fraction is kept by parsing the
  string (JavaScript `Date` is millisecond-only, so the fraction is re-appended
  after the local conversion).
- **Stored value unchanged** — `line.time` remains UTC ISO-8601; only the
  displayed text changes.
- **Flag names** — `show_date` / `show_utc_offset` (mirrors the user's "date"
  and "UTC shift").

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-logview-flags.md](./01-python-logview-flags.md) | `LogView` flags + serialization + Python tests |
| 2 | [02-frontend-local-time.md](./02-frontend-local-time.md) | `MessageView` local-time formatting + build wiring + JS tests |
| 3 | [03-docs-example-changelog.md](./03-docs-example-changelog.md) | Docs, example, branch changelog |

## Testing as you go

- Python: `uv run pytest py/tests/viz/test_log_view.py -q`
- JS: `node --check py/pytanga/viz/templates/views/message-view.js py/pytanga/viz/templates/views/build.js && node --test 'dev/src/js-tests/*.test.mjs'`
- Docs: `uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict`

## Non-goals

- No change to the stored `time` format (still UTC ISO-8601).
- No per-line timezone override — one set of flags per `LogView`.
- No change to `log_update` wire messages (flags ride in the initial layout
  node only).