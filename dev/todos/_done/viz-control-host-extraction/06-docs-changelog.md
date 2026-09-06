# Phase 6 — Docs + changelog

## Goal

Document the host architecture, record the change in the branch changelog, and
add the menu future-direction note.

## Files

- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- Edit: `docs/changelog/2026-09-03_feat-view-architecture.md` (append)

## Steps

- [x] **6.1 — Architecture doc**
  - Update the "Fixed contract" / add a "Host layer" section: controls, banners,
    dialogs, and the editor live in `py/pytanga/viz/_hosts.py` behind `OverlayHost`;
    `Visualizer` delegates; `_dispatch_control_event` routes to the owning host.
  - Add a **future direction** note: if menus gain a backend-visible "active
    element", add `value`/`on_change`/`on_activate` to `MenuView` (the
    `GroupView` + `on_toggle` pattern), not a `ControlView` conversion.

- [x] **6.2 — Changelog**
  - Append a `## Refactor` bullet describing the host extraction
    (`OverlayHost` + `ControlHost`/`BannerHost`/`DialogHost`/`EditorHost`), per
    `dev/workflows/changelog.md` (title already `# Changes since version 1.17.0`;
    re-check with `uv run python tools/last-release.py`).

- [x] **6.3 — Verify line count dropped**
  - Note `visualizer.py`'s post-refactor line count in the commit (sanity check
    the extraction actually shrank the file).

## Validation

`uv run mkdocs build --strict && uv run pytest py/tests/viz -q`

## Notes

- Final phase per `dev/workflows/create-plan.md`: docs + changelog last.
- No `docs/changelog/index.md` update at plan time (PR-time per
  `dev/workflows/pull-request.md`).
