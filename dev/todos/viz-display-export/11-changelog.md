# Phase 11 — Changelog

**Status:** Planned

## Goal

Add a changelog entry per `dev/workflows/changelog.md`.

## Files

- Add: `docs/changelog/YYYY-MM-DD_<short-hash>.md`
- Modify: `docs/changelog/index.md`

## Steps

- [ ] Create the changelog with the sections that apply:
      - **Bug Fixes** — `display_static()` no longer leaks styles / crashes
        the notebook (now renders via `<iframe srcdoc>`).
      - **Breaking Changes** — `host`/`port` moved to `start_server`;
        `open_figure` removed in favor of `open_snapshot`.
      - **Refactor** — consolidated display/export/serving naming
        (`snapshot`/`figure`/`glb`; `show`/`wait`/`start_server`/`stop_server`;
        `animation=` keyword) with deprecated aliases.
- [ ] Add the index entry to `docs/changelog/index.md`.

## Verification

- [ ] Changelog follows the structure in `dev/workflows/changelog.md`.
