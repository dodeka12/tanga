# Viz control tooltips — Overview

**Created:** 2026-11-09 | **Status:** Done | **Branch:** `feat/tooltips`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make tooltips first-class and runtime-switchable across the viz UI, driven by
the downstream feature request in `_input/pytanga-tooltip-requests.md`:

1. `ControlView.set_tooltip(text)` / `GroupView.set_tooltip(text)` that update a
   live tooltip (and clear it for an empty text);
2. one page-level `Visualizer.set_tooltips_enabled(bool)` switch that suppresses
   every framework tooltip, so an app needs no per-view bookkeeping;
3. a group tooltip that survives (and clears on) a layout re-push;
4. `GroupUI(tooltip=…)` reaching the nested group built by `ParamsView`;
5. an icon-only button whose label fallback respects the global switch while
   screen readers still get an `aria-label`;
6. `MenuView(tooltip=…)` so menu-bar headers can explain themselves.

## Architecture (short)

- A runtime tooltip change rides the **existing granular `control_state`**
  message (id-scoped), exactly like `enabled` / `visible` / `selected` /
  `title` — no `view_layout` re-push.
- The page-level switch is a **new `ui_options` message** (server → client).
  Its state lives in a small `UIOptionsHost` (`py/pytanga/viz/_hosts.py`), wired
  into the server like `ThemeHost`; it is sent once per session inside
  `_push_full_state` and broadcast on change.
- Browser side **every** framework tooltip goes through one helper,
  `applyTooltip(el, source)` in `templates/controls-panel.js`, which records the
  intended text in `data-tanga-tooltip`. `setTooltipsEnabled(bool)` re-syncs
  every recorded tooltip — that is what makes the switch global *and*
  reversible without per-view bookkeeping.

### Fixed wire/API contract (do not change across phases)

1. **`control_state` gains `tooltip`** (same message, id-scoped; `""` clears):

   ```json
   { "type": "control_state", "id": "radius", "tooltip": "Radius in mm" }
   ```

   Handled by `applyControlStateToElement` (control registry) and by a
   `setTooltip()` branch on the view registry (groups).

2. **`ui_options` message** (server → client, page-level):

   ```json
   { "type": "ui_options", "tooltips_enabled": true }
   ```

   Sent once per session in `_push_full_state` (right after `clear_all`, before
   `view_layout`) and broadcast by `Visualizer.set_tooltips_enabled(bool)`.

3. **Serialization**: `GroupView._serialize` and `MenuView._serialize` always
   emit `"tooltip"` (control views already do).  Empty string = cleared.

4. **Python API**
   - `ControlView.set_tooltip(text: str)` — sets `self.tooltip` *and*
     `self.control.tooltip`, pushes `{"tooltip": text}` via `_push_state`.
   - `Visualizer.set_control_tooltip(control_id: str, text: str)` — resolve +
     `set_tooltip`; unknown id is a no-op (mirrors `set_control_enabled`).
   - `GroupView.set_tooltip(text: str)` — mirror of `set_title`; pushes only
     `{"tooltip": …}` (never renames the title).
   - `MenuView(..., tooltip: str = "")`.
   - `Visualizer.set_tooltips_enabled(enabled: bool)` + read-only
     `Visualizer.tooltips_enabled`.

5. **JS helper API (`templates/controls-panel.js`)**
   - `applyTooltip(el, source)` — `source` is either a serialization object with
     a `tooltip` field **or** a plain string; sets/removes `el.title`, records
     `data-tanga-tooltip`.
   - `setTooltipsEnabled(enabled)` / `tooltipsEnabled()`.

6. **Icon-only button fallback** — `btn.title = tooltip || label || id` goes
   through the helper (so it is suppressed by the switch) and
   `btn.setAttribute('aria-label', …)` carries the accessible name.  No new
   Python kwarg.

## Decisions (confirmed)

- **Native `title` only.** No custom tooltip widget/framework. A `title` that
  is already on screen cannot repaint until the pointer leaves the element —
  that is a browser behaviour; the API makes the *stored* text correct so the
  next hover shows the new text.
- **Icon-only fallback kept**, switch-aware, plus `aria-label` (no per-button
  opt-out kwarg).
- **MenuView tooltips are static.** `menu` is not a reusable view type
  (`reconcile.js` `REUSABLE_TYPES`), so a re-push rebuilds it; no
  `MenuView.set_tooltip` / `update()` work.
- **Group tooltip push never renames**: `set_tooltip` pushes `{"tooltip": …}`
  only, `set_title` keeps pushing `{"title": …}`.
- The two tooltip copies on a control view (`ControlView.tooltip` and
  `Control.tooltip`, created together at construction) are always mutated
  together.
- The switch is **page-global** (no per-scene / per-layout variants).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-view-tooltip-python.md](./01-view-tooltip-python.md) | `ControlView`/`GroupView.set_tooltip`, always-emit `tooltip` for group/menu, `MenuView(tooltip=)`, `GroupUI` passthrough, `Visualizer.set_control_tooltip` + tests |
| 2 | [02-frontend-tooltip-core.md](./02-frontend-tooltip-core.md) | `applyTooltip` rewrite + `data-tanga-tooltip` + `setTooltipsEnabled`, `tooltip` in `applyControlStateToElement`, button/group/menu wiring, affordance sweep, `control_state` → `setTooltip` |
| 3 | [03-global-tooltips-switch.md](./03-global-tooltips-switch.md) | `UIOptionsHost`, `Visualizer.set_tooltips_enabled`, `ui_options` in `_push_full_state`, `viewer.js` handler + tests |
| 4 | [04-example-tooltips.md](./04-example-tooltips.md) | `py/examples/viz/ui/controls/tooltips.py` + regenerated example docs |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | User docs, architecture docs, branch changelog, PR prep |

## Testing as you go

```bash
uv run pytest py/tests/viz/test_views.py py/tests/viz/test_params_view.py \
               py/tests/viz/test_layout_api.py py/tests/viz/test_server_layout.py -q
node js/dev/tests/check-syntax.mjs
node --test js/dev/tests/*.test.mjs
uv run python tools/generate-example-docs.py      # after phase 4
uv run python tools/build-viewer-js.py --check    # after phase 5
uv run mkdocs build --strict                      # after phase 5
```

> The live frontend (`templates/controls-panel.js`, `templates/controls/`,
> `templates/views/`, `templates/viewer.js`) is served directly as ES modules;
> `js/tanga-viewer.js` is the *export* renderer bundle and does not include the
> control templates, so these edits create no bundle drift.

## Non-goals

- No custom tooltip widget, no tooltip positioning/delay/styling API.
- No tooltips on params **rows** (`RowSpec`), and none added to
  `LabelView` / `MarkdownView` / `ProgressBarView` / `FileChooserView`
  serialization (those controls carry no `tooltip` field today).
- No tooltips for the connection-status titles in `viewer.js`
  (`Connecting…` / `Reconnect failed`) — those are status text, not UI tooltips.
- No per-view / per-scene tooltip switch, and no layout re-push for a tooltip
  change.
- No `MenuView.set_tooltip` (menus are rebuilt on re-push).
