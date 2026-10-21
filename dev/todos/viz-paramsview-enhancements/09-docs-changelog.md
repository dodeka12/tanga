# Phase 9 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md`, `docs/dev/architecture/viz-controls-and-interactions.md`,
> `docs/dev/architecture/viz-theme-system.md`, and `dev/workflows/changelog.md`.
> Update the developer docs to record the new `ParamsView` capabilities.

## Goal

Document the enhancements for users and developers, update the example, and add
the changelog.

## Files

- **Edit** `docs/dev/architecture/viz-controls-and-interactions.md` — document the
  row-aware `ParamsView`, `ControlEvent.key/value`, `RowSpec`, `GroupUI`, coercion.
- **Edit** `docs/dev/architecture/viz-architecture.md` + `viz-theme-system.md` —
  the nested-group token and the theme constructor arg.
- **Edit** `docs/py/viz/ui/control-views.md` + `custom-themes.md` — the new API
  and tokens.
- **Edit** `py/examples/viz/ui/controls/params_view.py` — nested dataclass +
  button/status `RowSpec` + an `int`/`Enum` field to show coercion.
- **New** `docs/changelog/2026/10/DD_<branch>.md` — per `dev/workflows/changelog.md`.

## Steps

- [x] **9.1 — developer docs** — record the new `ControlEvent` fields, the
  row-aware `params_view` frontend, `RowSpec`/`extra_rows`, `GroupUI` nested
  groups, and `--tanga-group-nested-title-size`.
- [x] **9.2 — user docs** — document the new `ParamsView` methods, `RowSpec`,
  `GroupUI`, `ControlUI` fields (`on_change`, `coerce`, `visible`, `integer`,
  `unit`), and the `(value, label)` dropdown options.
- [x] **9.3 — example** — extend `params_view.py` and regenerate example docs
  (`uv run python tools/generate-example-docs.py`).
- [x] **9.4 — changelog** — branch changelog under `docs/changelog/2026/10/`.

## Validation

```bash
uv run mkdocs build --strict
```
