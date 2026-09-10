# Bug: `SplitView` collapses to zero height inside a `StackView` flow container

**Created:** 2026-09-06 | **Status:** Reported | **Branch:** `seating-plan-app`

A standalone bug description for the pytanga repo. Documents why a `SplitView`
placed directly inside a `StackView` (the natural "menu bar + split" layout, e.g.
`StackView("vertical", [MenuView(...), SplitView(...)])`) renders nothing — the
split collapses to zero height and none of its panes appear.

## Metadata

- Package: `tanga-py` (import name `pytanga`), version **2.0.0rc2**.
- Frontend: `pytanga/viz/templates/views/split-view.js` (absolute child
  positioning) · `stack-view.js` (flex assignment) · `flow-size.js` (`flowFlex`)
  · `view.js` (`preferredPx`). Python: `pytanga/viz/views.py` `SplitView`.
- Severity: high — any layout that nests a `SplitView` under a `StackView` /
  `GroupView` (menu bars, toolbars, sidebars) loses the split's entire content
  area; it renders as zero-height space.

## Summary

A `SplitView` lays its children out with `position: absolute` and does not
report an intrinsic cross-axis size, so when it is a child of a flow container
(`StackView`), it is sized as `flex: 0 1 auto` with an `auto` basis of 0. The
result is a split that is exactly 0 px tall (or wide, for a vertical split in a
horizontal stack) and invisible, even though its children have real content.

## Steps to reproduce

```python
from pytanga.viz import (
    ButtonView, GroupView, MenuView, SceneView, Size, SplitView,
    StackView, TableView, Visualizer,
)

viz = Visualizer(reuse_existing=False, title="Split-in-stack repro", space_dim=2)

bar = MenuView(mode="bar", children=[
    MenuView("File", [ButtonView("open", label="Open")]),
])
body = SplitView(
    "horizontal",
    sizes=[Size.percent(50), Size.percent(50)],
    children=[
        GroupView("Pupils", [TableView("pupils", columns=["name"], rows=[["Alice"]])]),
        SceneView(""),
    ],
)

viz.show(layout=StackView("vertical", [bar, body]))
viz.wait()
```

1. Run the script.
2. Observe the browser page.

### Expected

A horizontal menu bar at the top, with the pupil table and the scene pane
filling the rest of the window below it.

### Actual

Only the menu bar is visible. The `SplitView` (and both of its panes) is 0 px
tall — nothing appears below the menu bar.

## Root cause

1. `SplitView` positions its children absolutely (`split-view.js:100`), so the
   children do not contribute to the split's own natural size:

   ```js
   el.style.position = 'absolute';
   ```

   `SplitView` overrides `minSizePx` (`split-view.js:68`) to derive a minimum
   from its children, but it does **not** override `preferredPx` for the cross
   axis, so `View.preferredPx` (`view.js:115`) returns `null`.

2. `StackView` is a flex container. For each child it sets
   (`stack-view.js:76`):

   ```js
   view.el.style.flex = flexCss(flowFlex(pref));
   ```

   where `pref` is the child's `preferredHeight` (vertical stack). With
   `preferredHeight == null`, `flowFlex` (`flow-size.js:16-18`) maps to:

   ```js
   return { grow: 0, shrink: 1, basis: 'auto' };   // CSS "0 1 auto"
   ```

3. Net effect: the split gets `flex: 0 1 auto` with an `auto` basis, but because
   its children are absolutely positioned its `auto` basis is 0 — so it is laid
   out at 0 px height and never grows (only a `fr` preferred size sets `grow`).

The same applies to a vertical `SplitView` inside a horizontal `StackView`
(zero width), and to a `GroupView` (a titled `StackView`) child.

## Suggested fix

One (or a combination) of:

- **Report an intrinsic cross-axis size.** Override `preferredPx` in
  `SplitView` to return a size derived from its children for the non-split axis
  (mirroring the existing `minSizePx` derivation), so `flex: 0 1 auto` gets a
  real `auto` basis and the split renders at its content size by default.

- **Grow split children in flow containers by default.** Have `StackView`
  (or `flowFlex`) treat a child whose main-axis preferred size is unset but
  which has no intrinsic main-axis size as `fr(1)`-like, so a `SplitView` fills
  the leftover space instead of collapsing. (This is the more ergonomic default
  for the common "menu + split" layout, but changes current semantics.)

- **Document it.** At minimum, document that a `SplitView` placed inside a
  `StackView`/`GroupView` must set an explicit flexible preferred size, e.g.
  `SplitView(..., preferred_height=Size.fr(1))`.

## Workaround

Applied downstream in `seating-plan-app`: set `preferred_height=Size.fr(1)` on
the `SplitView` used as the body under the menu bar + toolbar, so it grows to
fill the remaining height:

```python
body = SplitView(
    "horizontal",
    sizes=[Size.percent(42), Size.percent(58)],
    preferred_height=Size.fr(1),
    children=[...],
)
```
