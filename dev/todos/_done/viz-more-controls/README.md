# Viz More Controls — Overview

**Created:** 2026-08-27 | **Status:** Done | **Branch:** `feat/more-controls`

## Goal

Extend the interactive control system (`py/pytanga/viz/_controls.py` + the JS
control factories) with four new controls — single-line text, multi-line text,
color picker, and checkbox — plus icon and tooltip support:

- **Button** gains an optional icon (alongside the label) and an `icon_only`
  mode (a small square button).
- **Every control** gains an optional `tooltip`.
- **Control groups** gain an optional title-bar icon and tooltip.
- **Icons** are addressed as `family:name` strings (`material:settings`,
  `uc:▶`) so new collections (e.g. Font Awesome) can be added later without
  changing the wire format. Google Material Icons are loaded from the online
  Google Fonts stylesheet (no font files shipped); Unicode symbols are rendered
  as literal text.

## Architecture (short)

- **Python is a pass-through for icons.** Icon ids are opaque `family:name`
  strings; `_icons.py` only defines the enums (for autocompletion) and a tiny
  grammar helper. The *family → font URL / render mode* mapping lives in one JS
  helper (`createIconElement`) so new families are added there, not in the
  Python model or serialization.
- **Tooltips use the native `title` attribute**, set on the control's wrapper
  element (the browser's ancestor-chain lookup shows it over the whole control).
  Icon-only buttons put `tooltip || label` on the `<button>` for accessibility.
- **Controls keep flowing through the existing channels** — `controls_define`
  (fixed panel + attached CSS2D groups), `banner_define` (banner options), and
  the `view_layout` control views — because serialization is centralized in
  `_serialize_one_control` / `serialize_controls`.

## Canonical wire contract (fixed up front; both sides implement against this)

### Icon id grammar

```
<family>:<name>          material:settings   uc:▶
<name>                   settings            (bare → family "material")
```

New families add a Python enum (optional, for autocompletion) + one case in
`createIconElement` — no wire change.

### Control definitions (`controls_define.controls[]`)

```json
{ "id": "name", "kind": "text", "label": "Name", "value": "", "placeholder": "", "tooltip": "…" }
{ "id": "notes", "kind": "textarea", "label": "Notes", "value": "", "placeholder": "", "rows": 4, "tooltip": "…" }
{ "id": "color", "kind": "color", "label": "Color", "default": "#ff0000", "tooltip": "…" }
{ "id": "wire", "kind": "checkbox", "label": "Wireframe", "default": false, "tooltip": "…" }
{ "id": "reset", "kind": "button", "label": "Reset", "icon": "material:refresh", "icon_only": false, "tooltip": "…" }
```

- `tooltip` is omitted when empty; `icon` is omitted when unset; `icon_only` is
  always a boolean.
- Existing `slider` / `dropdown` / `file_chooser` shapes are unchanged except
  for the optional `tooltip`.

### Group definitions (`controls_define.groups[]`)

```json
{ "id": "g", "title": "Controls", "controls": ["name", "reset"],
  "position": "bottom-right", "collapsed": false, "parentId": null,
  "icon": "material:settings", "tooltip": "…" }
```

### Events (client → server, unchanged)

- `control:change` with `value` — text/textarea/color (string), checkbox
  (boolean), slider (float), dropdown (string).
- `control:click` with no value — button (with or without icon).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-icon-model.md](./01-python-icon-model.md) | `_icons.py`: `EIconMaterial`/`EIconUC` enums, `Icon` alias, grammar helpers (+ tests) |
| 2 | [02-python-control-group-model.md](./02-python-control-group-model.md) | New control dataclasses, `Button` icon/icon_only, `Control.tooltip`, `ControlGroup` icon/tooltip, serialization (+ tests) |
| 3 | [03-visualizer-api.md](./03-visualizer-api.md) | `add_*` methods + tooltip/icon params, `_scene_handle` forwarding, `__init__.py` exports |
| 4 | [04-frontend-control-factories.md](./04-frontend-control-factories.md) | `createIconElement`, extended `createButton`, 4 new factories, tooltip, CSS, Material link, attached dispatch |
| 5 | [05-frontend-group-title-and-banner.md](./05-frontend-group-title-and-banner.md) | Group title-bar icon/tooltip (panel + attached), banner `_buildControl` |
| 6 | [06-python-views-parity.md](./06-python-views-parity.md) | `views.py`: new control views, `ButtonView` icon, `ControlView.tooltip` (+ tests) |
| 7 | [07-frontend-views-parity.md](./07-frontend-views-parity.md) | JS control views + `build.js` wiring |
| 8 | [08-docs-changelog.md](./08-docs-changelog.md) | Docs + changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/test_controls.py
  py/tests/viz/test_views.py py/tests/viz/test_icons.py -q`.
- **DOM/browser modules** (`controls-panel.js`, `controls-attached.js`,
  `views/*-view.js`, `banner-view.js`) are validated via the existing manual
  viewer and browser smoke pages; the repo has no DOM test harness.
- Every phase ends with a runnable validation command before the next phase.

## Guiding decisions / no-refactor rule

- The wire contract above is **fixed now**; later phases implement *against* it
  and never change it.
- Icon ids are opaque on the Python side; the family→font mapping lives only in
  `createIconElement`.
- Use native `title` for tooltips (no custom tooltip CSS); add styled tooltips
  later only if needed.
- Keep new controls symmetric with existing ones: every control has a dataclass
  + serialization branch + `add_*` method + JS factory + (view) counterpart.
