# Phase 7 — Docs + changelog (item 6)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md`, `viz-architecture.md`,
> `viz-theme-system.md`, and `dev/workflows/changelog.md`.  Record the new
> `ParamsView`/`GroupView` capabilities (and update the architecture docs for the
> `control_state` group routing added in Phase 3).

## Goal

Document the follow-up features for users and developers, and add the changelog.

## Files

- **Edit** `docs/dev/architecture/viz-controls-and-interactions.md` — `full_width`/
  `label`, dotted keys, group `visible`/`enabled`/`title` + the `control_state`
  `{enabled}`/`{title}` view routing, nested `extra_rows`.
- **Edit** `docs/dev/architecture/viz-architecture.md` + `viz-theme-system.md` — the
  `.tanga-group-disabled` class and any new token.
- **Edit** `docs/py/viz/ui/control-views.md` — the new `ControlUI.full_width`,
  `ButtonUI.label`, `GroupUI.extra_rows`, dotted row API, group row state.
- **New** `docs/changelog/2026/10/21_paramsview-followup.md` — branch changelog.

## Steps

- [x] **7.1 — developer docs** — document `full_width`/`label`, dotted keys +
    `key_prefix`, the `GroupView` state methods, and the `viewer.js`
    `control_state {enabled}`/`{title}` routing.
- [x] **7.2 — user docs** — document the new `ControlUI`/`ButtonUI`/`GroupUI`
    fields, the dotted row API, `set_state` rebind, and full-width rendering.
- [x] **7.3 — changelog** — branch changelog under `docs/changelog/2026/10/`
    (title per `uv run python tools/last-release.py`).

## Validation

```bash
uv run mkdocs build --strict
```
