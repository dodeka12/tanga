# Viz ToolbarView — Overview

**Created:** 2026-09-03 | **Status:** Done | **Branch:** `feat/view-architecture`

## Goal

Add a `ToolbarView` — a horizontal `StackView` with a thin border, a
parameterizable surrounding margin, configurable element spacing, and a setting
to align its controls left / right / block-centered / equally spaced.  Back it
with **shared string enums** for the layout axes so `StackView`, `GroupView`,
`MenuView`, and `ToolbarView` all reuse the same enum vocabulary.

## Architecture (short)

- **Backend model** — `views.py` defines the layout enums and `ToolbarView` as
  a `StackView` subclass (`_node_type = "toolbar"`); it serializes through the
  existing `serialize_layout` → `view_layout` path.
- **Frontend** — `views/build.js` maps `node.type === "toolbar"` to a new
  `views/toolbar-view.js` class (extends `StackView`); a
  `themes/views/toolbar-view.css` sheet provides the border/radius and is
  registered in `themes/registry.json`.
- **One control path** — unchanged; `ToolbarView` is just another layout
  container rendered by `view_layout`, per
  `docs/dev/architecture/viz-controls-and-interactions.md`.

## Fixed contract (up front)

### 1. Shared layout enums (`StrEnum`, replacing the current `Literal` aliases)

```python
class EStackDirection(StrEnum):
    VERTICAL = "vertical"; HORIZONTAL = "horizontal"; WRAP = "wrap"

class EStackAlign(StrEnum):
    START = "start"; CENTER = "center"; END = "end"; STRETCH = "stretch"

class EStackJustify(StrEnum):
    START = "start"; CENTER = "center"; END = "end"
    SPACE_BETWEEN = "space-between"
    SPACE_AROUND  = "space-around"
    SPACE_EVENLY  = "space-evenly"
```

`StackView` / `GroupView` / `MenuView` switch their `direction` / `align` /
`justify` annotations and defaults to these enums.  Because `StrEnum` members
are `str`, plain strings (e.g. `StackView("horizontal", justify="start")`) keep
working and the serialized JSON values are byte-for-byte unchanged.

### 2. `ToolbarView`

```python
ToolbarView(
    children,
    *,
    margin=Size.px(6),          # SizeSpec | None — inner spacing around the controls
    border=True,                # thin 1px border (--tanga-border-subtle)
    gap=None,                   # int px | None — spacing between controls
    align=EStackAlign.CENTER,   # cross-axis (vertical) alignment
    justify=EStackJustify.START,  # "left" | "right" | "center" | "space-evenly"
    **kwargs,
)
```

`direction` is fixed to `"horizontal"`; there is no title or collapse (that is
`GroupView`).  The four requested alignments map onto `justify`:
**left** → `START`, **right** → `END`, **block center** → `CENTER`,
**equally spaced** → `SPACE_EVENLY`.

### 3. Serialized node

```json
{"type": "toolbar", "direction": "horizontal", "gap": 6, "align": "center",
 "justify": "space-evenly", "margin": {"value": 6.0, "unit": "px"}, "border": true,
 "children": [...]}
```

## Decisions (confirmed)

- Use the **shared** `EStackJustify` (not a toolbar-only `LEFT`/`RIGHT` enum) —
  the four toolbar alignments are the `START`/`END`/`CENTER`/`SPACE_EVENLY`
  members.
- `margin` = inner padding between the border and the controls (not outer CSS
  margin); uniform on all sides, expressed as a `SizeSpec`.
- `border` = simple on/off toggle using the existing `--tanga-border-subtle`
  token (no thickness/color configuration).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-layout-enums.md](./01-layout-enums.md) | Replace `StackDirection`/`StackAlign`/`StackJustify` Literals with shared `EStack*` `StrEnum`s |
| 2 | [02-toolbar-view-model.md](./02-toolbar-view-model.md) | Add the `ToolbarView` backend model + serialization |
| 3 | [03-toolbar-view-frontend.md](./03-toolbar-view-frontend.md) | Frontend `toolbar-view.js` + `build.js` + theme CSS |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Docs, example, changelog |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/ -q` (per-phase subsets in each phase)
- **JS:** `node --check <files>` and `node --test 'dev/src/js-tests/*.test.mjs'`
- **Docs:** `uv run mkdocs build --strict` and
  `uv run python tools/generate-example-docs.py --check`

## Non-goals

- No conversion of `SplitView`'s `Orientation` Literal or `MenuView.mode`
  Literal — only the stack `direction`/`align`/`justify` triples.
- No configurable border color/thickness; `border` is on/off only.
- No per-axis margins (uniform `SizeSpec` only).
- No title bar, icon, or collapse on `ToolbarView` (that is `GroupView`).
