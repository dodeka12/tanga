# Viz progress bar control — Overview

**Created:** 2026-09-26 | **Status:** Done | **Branch:** `feat/ui-progress-bar`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add a themable `ProgressBarView` control following the existing control
architecture — a `ProgressBar` control wrapped by a `ProgressBarView(ControlView)`
— with a **determinate** mode (title + `total` steps + progress) and an
**indeterminate** animation (something is running), a title above the bar, and
an optional status text line below it.  Ships with an example, user docs, and a
changelog entry.

## Architecture (short)

- Reuses the existing control stack end-to-end: `Control` model
  (`_controls.py`) → `ControlView` subclass (`views/control_views.py`) → public
  exports (`viz/__init__.py`, `views/__init__.py`, `views/functions.py`) →
  JS DOM factory (`templates/controls/progress-bar.js`) → JS view
  (`templates/views/progress-bar-view.js`) + `build.js` dispatch → theme CSS
  (`templates/themes/controls/progress-bar.css`).
- Runtime updates reuse the existing `control_update` channel (the
  `ControlView.set_value` → `_push` → `applyControlValue` path), mirroring how
  `Table` carries a structured value dict.
- Themeing follows `docs/dev/architecture/viz-theme-system.md`: stable class
  names + `var(--tanga-*)` tokens, one component sheet, registered in
  `registry.json`.

### Fixed wire/API contract (do not change across phases)

1. **`ProgressBar` control** — `kind: str = "progress"`; fields
   `title: str = ""`, `value: float = 0.0`, `total: int = 0`,
   `indeterminate: bool = False`, `text: str = ""`.  `_fields()` serializes all
   five.
2. **Value shape** — `ProgressBar.get_value()` returns (and `set_value()`
   accepts) the dict `{"title", "value", "total", "indeterminate", "text"}`.
   A bare number to `set_value` sets `value` only.  This dict is what
   `control_update` carries.
3. **View node** — `ProgressBarView._node_type = "progress_bar_view"`;
   serialized fields are `title`, `value`, `total`, `indeterminate`, `text`
   (plus the shared `id`/`label`/`tooltip`/size specs).
4. **Mode** — `indeterminate` selects the mode: `True` animates; `False`
   renders a determinate bar (fill = clamped `value/total`, empty when
   `total <= 0`, percent readout).
5. **Theming** — stable classes `.tanga-progress`, `.tanga-progress-title`,
   `.tanga-progress-track`, `.tanga-progress-fill`, `.tanga-progress-value`,
   `.tanga-progress-text`, plus `.tanga-progress-indeterminate`; no inline
   appearance.  Colors come from `var(--tanga-*)` tokens so all themes apply
   automatically.
6. **Read-only** — the progress bar registers no `on_*` handlers; it is a
   backend-driven display control (like `Label`/`Markdown`).

## Decisions (confirmed)

- One control covers both modes; `indeterminate=True` selects the animated
  bar, otherwise the determinate bar shows `value`/`total` (empty when
  `total<=0`) and a percent.
- Progress value is a `float` (steps may be fractional); `total` is an `int`.
- The title and status text are `ProgressBar` fields (`title` above, `text`
  below), not the generic control `label`.
- Read-only: no `on_change`/`on_click`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-progress-control-model.md](./01-progress-control-model.md) | `ProgressBar` control model + tests |
| 2 | [02-progress-view-python.md](./02-progress-view-python.md) | `ProgressBarView` + exports + `control_to_view` + tests |
| 3 | [03-progress-frontend.md](./03-progress-frontend.md) | JS factory + JS view + `build.js` dispatch |
| 4 | [04-progress-theme-css.md](./04-progress-theme-css.md) | theme CSS + registry + theme test |
| 5 | [05-progress-example.md](./05-progress-example.md) | example + docs gallery regen |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | user docs + changelog |

## Testing as you go

```bash
uv run pytest py/tests/viz -q                     # Python side
node js/dev/tests/check-syntax.mjs                # JS syntax
uv run python tools/generate-example-docs.py --check   # example gallery (after phase 5)
uv run mkdocs build --strict                      # docs (after phase 6)
```

## Non-goals

- No progress bar support in transient `Banner`/`Dialog` control rows (it is a
  layout `ControlView`, not a banner control).
- No indeterminate-adjacent "activity" widget beyond the animated bar.
- No new wire message type — runtime updates ride the existing `control_update`.
