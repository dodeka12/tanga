# Phase 11 — Changelog

**Status:** Done

## Goal

Add a changelog entry per `dev/workflows/changelog.md`.

## Files

- Add: `docs/changelog/YYYY-MM-DD_<short-hash>.md`
- Modify: `docs/changelog/index.md`

## Steps

- [x] Create the changelog with the sections that apply:
      - **Bug Fixes** — `display_static()` no longer leaks styles / crashes
        the notebook (now renders via `<iframe srcdoc>`).
      - **Breaking Changes** — `host`/`port` deprecated on `Visualizer(...)`;
        `open_figure` replaced by `open_snapshot`.
      - **Refactor** — consolidated display/export/serving naming
        (`snapshot`/`figure`/`glb`; `show`/`wait`/`start_server`/`stop_server`;
        `animation=` keyword) with deprecated aliases.
- [x] Add the index entry to `docs/changelog/index.md`.

## Verification

- [x] Changelog follows the structure in `dev/workflows/changelog.md`.
