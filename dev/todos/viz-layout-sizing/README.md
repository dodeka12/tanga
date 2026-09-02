# Viz Layout Sizing — Overview

**Created:** 2026-09-02 | **Status:** Planned | **Branch:** `feat/file-chooser-update`

> Note: this work is about the declarative layout model, not the file chooser.
> It is recommended to branch a dedicated `feat/viz-layout-sizing` from here
> before implementing.

## Goal

Give the declarative `StackView`/`GroupView` layout the same "sizes per object,
and whether an object extends to fill the available space" flexibility that
HTML flexbox offers — but reduced to a small, principled surface. Concretely,
after this plan a caller can:

- make a child (e.g. a multi-line `TextAreaView`) fill the remaining space in a
  horizontal `StackView`;
- configure spacing between children (`gap`);
- align children on the cross axis (`align`) and along the main axis
  (`justify`);
- pin a child's size (`min == max`) without disabling splitters on its far side
  in a `SplitView`.

This closes the sizing gaps behind `_input/pytanga-dialog-width-not-controllable.md`
and `_input/pytanga-splitview-fixed-pane-disables-unrelated-splitter.md`.

## Architecture (short)

Two-layer mirror, as today: the Python tree in `py/pytanga/viz/views.py`
serializes to `view_layout`; the JS tree in `py/pytanga/viz/templates/views/`
materializes it.

- **Children own size hints** (`min_*`/`max_*`/`preferred_*`, already present);
  **containers own layout policy** (`gap`, `align`, `justify`).
- **`fr` becomes the "grow" unit.** A child's `preferred_<main axis>` is
  interpreted by a flow container as flex, reusing the existing `Size` units —
  no new unit type.
- **Splitter movability** becomes "nearest movable neighbor": a splitter trades
  space between the nearest non-fixed panes on each side, so a fixed pane keeps
  its size without walling off panes beyond it.

## Fixed contract (up front; both sides implement against this)

### Per-child flex (flow containers only: `stack` / `group`)

A child's `preferred_*` along the container's **main axis** maps to CSS flex
(`flex: <grow> <shrink> <basis>`):

| `preferred_<main>`       | `flex`        | meaning                                  |
|--------------------------|---------------|------------------------------------------|
| `None` / `Size.auto()`   | `0 1 auto`    | natural size, may shrink to `min`        |
| `Size.fr(n)`             | `n 1 0`       | grow to fill leftover, weighted by `n`   |
| `Size.px(v)`             | `0 0 <v>px`   | fixed basis, no grow/shrink              |
| `Size.percent(v)`        | `0 0 <v>%`    | fixed basis, no grow/shrink              |

`min_*`/`max_*` keep clamping the result (already applied as CSS
`min-width`/`max-width`/`min-height`/`max-height`). For `fr`, the container
additionally sets `min-<main>` to `0` **only when the child has no explicit
`min_<main>`**, so a growing child can shrink below its content size.

Cross-axis "fill" is the container's `align` (below), matching HTML's
`align-items: stretch` default.

### New `stack` / `group` node fields

```json
{ "type": "stack", "id": "s3", "direction": "vertical",
  "gap": null, "align": "stretch", "justify": "start",
  "min_width": null, "max_width": null, "min_height": null, "max_height": null,
  "preferred_width": null, "preferred_height": null,
  "children": [ ... ] }
```

- `gap` — `int | null` px; `null` = default `4` px, `0` removes spacing.
- `align` — `"start" | "center" | "end" | "stretch"` (default `"stretch"`).
- `justify` — `"start" | "center" | "end" | "space-between" | "space-around" |
  "space-evenly"` (default `"start"`).

`group` nodes carry the same three fields (they are stacks with chrome).

### Control floors move to Python

`ControlView` defaults `min_width=Size.px(120)` and `min_height=Size.px(32)`
in Python (overridable; `None` disables). The JS `ControlView` no longer
hardcodes them, and `build.js::applySizeSpecs` assigns all six size fields
unconditionally (so a `null` from Python clears any JS default). The JS
`ControlView` no longer sets `flexShrink: '0'`.

### `SpacerView`

In a flow container, a `SpacerView` is `flex: 1 1 0` (grows along the main
axis). In a `SplitView` it is positioned absolutely by the splitter, so the
flex declaration is inert there.

### SplitView splitters

A splitter is `movable` iff there is a **non-fixed child on each side**, where
"sides" search across fixed children. Dragging redistributes space between the
nearest non-fixed child on each side, never resizing a fixed child.

## Decisions (confirmed)

- **Use `fr` as the grow hint** (recommended; reuses the existing `Size`
  vocabulary and expresses weighting for free).
- **`gap` is a plain pixel `int`** (`None` = default `4` px), not a `Size`, to
  keep spacing dead simple.
- **Defaults match HTML**: `align="stretch"`, `justify="start"`.
- **SplitView fix is the "nearest movable neighbor" model** with no new API
  flag. This intentionally changes the existing resolver test
  "a fixed middle pins its two neighbors" (the whole point is to stop pinning).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-sizing-contract.md](./01-python-sizing-contract.md) | Python `gap`/`align`/`justify` + control floors + serialization (+ tests) |
| 2 | [02-flow-flex-helper.md](./02-flow-flex-helper.md) | Pure JS flex resolution helper + gap parametrization (+ tests) |
| 3 | [03-frontend-flex-layout.md](./03-frontend-flex-layout.md) | Wire flex/gap/align/justify into DOM views + `build.js` (+ smoke) |
| 4 | [04-splitview-fixed-pane.md](./04-splitview-fixed-pane.md) | Nearest-movable-neighbor splitter semantics (+ tests) |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Docs, example, changelog, full validation |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/test_views.py -q` (phase 1), then the
  full `uv run pytest py/tests/viz/ -q` at the end.
- **JS pure modules:** `node --test 'dev/src/js-tests/*.test.mjs'` (size, flow,
  stack-size, split-resolver).
- **DOM/browser modules** (`stack-view.js`, `control-view.js`, `split-view.js`)
  are validated by browser smoke pages under `dev/src/js-tests/*.html`; add one
  per phase that changes DOM behavior.
- **Docs:** `uv run mkdocs build --strict`.

## Non-goals

- `MenuView` gap/align/justify — its bar/panel layout is specialized; out of
  scope for now.
- Full flexbox surface (`order`, `align-self`, `align-content`, `flex-flow`,
  `margin` tricks, `flex-wrap` beyond the existing `wrap` direction).
- Cross-axis sizing in `wrap` mode beyond natural content sizing.
- Removing the legacy panel-control path (`viz.add_slider`, `controls_define`).
