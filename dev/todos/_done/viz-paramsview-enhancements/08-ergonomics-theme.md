# Phase 8 — Ergonomics + theme

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-theme-system.md` (theme selection) and
> `docs/py/viz/visualizer/visualizer.md` (Visualizer API).  `Visualizer(theme=…)`
> sets the theme before the first `theme_define`.

## Goal

Tooltips/descriptions from the dataclass, a `theme=` constructor arg, and (if
cheap) a per-`ParamsView` density flag.

## Files

- **Edit** `py/pytanga/viz/views/params_view.py` — tooltip/description fallback.
- **Edit** `py/pytanga/viz/visualizer.py`, `py/pytanga/viz/_app.py` — `theme=`.
- **Edit** `py/tests/viz/test_params_view.py`, `py/tests/viz/test_themes.py`.

## Steps

- [x] **8.1 — tooltips from the dataclass**
  - Fall back to the field's docstring / `metadata["description"]` when no
    `tooltip` is set; optional `title_from_name=True` (snake_case → Title Case).
- [x] **8.2 — `theme=` constructor arg**
  - `Visualizer(theme="compact")` / `VisualizerApp(theme=…)` set the theme before
    the browser connects (validate + store, push on `theme_define`).
- [x] **8.3 — per-View density**
  - `ParamsView(dense=True)` adds a class consumed by a compact CSS override.
- [x] **8.4 — tests**
  - Docstring→tooltip; `Visualizer(theme=…)` defaults correctly.

## Validation

```bash
uv run pytest py/tests/viz/test_params_view.py py/tests/viz/test_themes.py -q
```
