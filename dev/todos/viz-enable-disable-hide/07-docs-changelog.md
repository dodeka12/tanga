# Phase 7 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Update the architecture docs, user docs, and changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- Edit: `docs/py/viz/ui/controls.md`
- Edit: `docs/py/viz/ui/control-views.md`
- Edit: `docs/py/viz/ui/runtime-updates.md`
- Edit: `docs/py/viz/entities/index.md`
- Edit: `docs/py/viz/interaction/object-interaction.md`
- Edit: `docs/py/viz/entities/active-elements/index.md`
- New: `docs/changelog/2026/09/DD_feat-viz-enable-disable-hide.md`

## Steps

- [x] **7.1 — Architecture docs**
  - `viz-architecture.md`: document the `visible` aspect, `Scene.set_visible`,
    and the entity hide API in the data-flow / extension-recipe sections.
  - `viz-controls-and-interactions.md`: document `Control.enabled/visible`,
    `ControlView` setters, and the `control_state` push path (next to the
    `control_update` / per-handler-enable sections).

- [x] **7.2 — User docs**
  - `docs/py/viz/ui/controls.md` + `control-views.md` + `runtime-updates.md`:
    control enable/disable/hide.
  - `docs/py/viz/entities/index.md`: entity visibility (`set_visible`/`hide`).
  - `docs/py/viz/interaction/object-interaction.md` +
    `active-elements/index.md`: `ActSceneObject.set_enabled/enable/disable`.

- [x] **7.3 — Changelog**
  - Create `docs/changelog/2026/09/DD_feat-viz-enable-disable-hide.md` per
    `dev/workflows/changelog.md` (title from
    `uv run python tools/last-release.py`; `## New Features` bullet).

## Validation

```bash
uv run mkdocs build --strict
```

## Notes

- Finalize the changelog filename to the hash form at PR time per
  `dev/workflows/pull-request.md`.
