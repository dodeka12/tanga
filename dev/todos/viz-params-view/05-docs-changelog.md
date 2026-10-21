# Phase 5 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (extension recipe index),
> `docs/dev/architecture/viz-controls-and-interactions.md` (control view list), and
> `dev/workflows/changelog.md`.  Update the developer docs to record the new
> `params_view` view type and the `Control.hide_label` field.

## Goal

Document `ParamsView`/`ControlUI`/`param_ui` for users and developers, and add the
branch changelog entry.

## Files

- **Edit** `docs/dev/architecture/viz-architecture.md` — note the `params_view`
  view type in the control/extension-recipe area.
- **Edit** `docs/dev/architecture/viz-controls-and-interactions.md` — add
  `ParamsView` to the control-view list and `hide_label` to the control contract.
- **Edit** `docs/py/viz/ui/control-views.md` — a `ParamsView` section (dict +
  dataclass, `ControlUI` hierarchy, `param_ui()` + raw `field()`, inference table).
- **New** `docs/changelog/2026/10/DD_<branch>.md` — per `dev/workflows/changelog.md`.

## Steps

- [x] **5.1 — developer docs**
  - `viz-architecture.md`: add `ParamsView` to the "Add a control"/recipe summary.
  - `viz-controls-and-interactions.md`: list `ParamsView` and document the
    `hide_label` serialized field (label-less control inside a params row).
- [x] **5.2 — user docs**
  - `control-views.md`: new `ParamsView` section with the API (incl. `styles:
    dict[str, ControlUI]`), the `ControlUI` classes, the `param_ui()` helper, the
    raw `field()` alternative, and the inference table.
- [x] **5.3 — changelog**
  - `docs/changelog/2026/10/DD_<branch>.md` with `## New Features` (ParamsView) and
    any `## Breaking Changes`/`## Refactor` (none expected; `Control.hide_label` is
    additive).  Title from `uv run python tools/last-release.py`.

## Validation

```bash
uv run mkdocs build --strict
```
