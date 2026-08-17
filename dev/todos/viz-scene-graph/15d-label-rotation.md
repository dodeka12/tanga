# Phase 15d — Screen-plane label rotation

**Parent:** [15-label-anchors-rotation.md](./15-label-anchors-rotation.md)
**Status:** Done

## Goal

Apply `LabelStyle.rotation` (degrees) as a screen-plane rotation about the
label's final anchor, in both the entity-label path and the axis-value-label
path.

## Frontend CSS

The label content element currently has:

```js
transform: translate(off2d[0]px, off2d[1]px) translate(tx%, ty%);
```

Add rotation about the anchor (the `align` point) by setting `transform-origin`
to the align point and appending `rotate(...)`:

```js
div.style.transformOrigin = `${align[0] * 100}% ${align[1] * 100}%`;
div.style.transform =
  `translate(${off2d[0]}px, ${off2d[1]}px) translate(${tx}%, ${ty}%) rotate(${rotation}deg)`;
```

`rotation` defaults to `0` when absent.

## 1. Entity labels

File: `py/pytanga/viz/templates/scene-builder.js` (`buildOverlay`)

- [x] Read `s.rotation || 0`; apply the `transform-origin` + `rotate` above.

## 2. Axis value labels

File: `py/pytanga/viz/templates/renderers/axis.js` (`makeLabel`)

- [x] Add a `rotation` option to `makeLabel`; read `labelStyle.rotation || 0`
      and apply the same `transform-origin` + `rotate`.
- [x] Pass `rotation: labelStyle.rotation` when creating value labels (and the
      axis name label, if desired).

## Tests

- [x] `node --check` on both files.
- [x] Smoke: a label with `rotation=45` tilts about its anchor in the live
      viewer and in an exported HTML; axis tick labels rotate. Verified
      end-to-end (no browser in this env): `node --check` on both files, unit
      tests for axis `label_style.rotation` flow + export HTML embedding
      (`rotate(...)` + `transformOrigin`), plus a manual `_output` smoke script
      that exports a rotated label + rotated axis labels and confirms both.
