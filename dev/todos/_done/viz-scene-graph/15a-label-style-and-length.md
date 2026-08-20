# Phase 15a — `LabelStyle.along`/`rotation` fields + line length resolution

**Parent:** [15-label-anchors-rotation.md](./15-label-anchors-rotation.md)
**Status:** Done

## Goal

Add the two new `LabelStyle` fields (`along`, `rotation`) and a backend line
length resolver, so the later phases can build on them.

## 1. `LabelStyle.along` and `LabelStyle.rotation`

File: `py/pytanga/viz/_styles/_overlay_styles.py`

- [x] Add `along: float | tuple[float, float] | tuple[float, float, float] | None = None`
      (fraction(s) along the entity's extent).
- [x] Add `rotation: float | None = None` (degrees, screen-plane, clockwise).
- [x] Extend `to_dict()`:
      - `along`: scalar → number; tuple/list → `list(...)`.
      - `rotation`: number.

These fields flow through the existing `LabelStyle` serialization and style
merge (`_merge_style`, `_resolve_label_style`) automatically, because those
iterate over `__dict__` / `to_dict()`.

## 2. Per-kind default for Line

File: `py/pytanga/viz/_style_dict.py`

- [x] In `_make_default_label_styles()`, next to the Point override, add:
      `result["Line"].along = 0.5` (midpoint is the natural line label anchor).

## 3. Serialization: strip `along`, keep `rotation`

File: `py/pytanga/viz/_nodes.py`

- [x] In `VizOverlayObject.serialize()`, where `offset_local` is popped, also
      `style.pop("along", None)`. `rotation` stays (the frontend applies it).

## 4. `resolve_line_length`

File: `py/pytanga/viz/serializer.py`

- [x] Add `resolve_line_length(line, *, styles_map=None, props=None) -> float`:
      finite `line.length` → it; else `props["style"].length` → it; else
      `_style_for_kind("Line", styles_map).length` → it; else `20.0`.
- [x] Use it in `_serialize_line`: `props["length"] = resolve_line_length(...)`
      (replaces the `0.0 if ent.length is None` sentinel).

## Tests

- [x] `LabelStyle(along=0.5, rotation=45).to_dict()` → `along == 0.5`,
      `rotation == 45`.
- [x] `LabelStyle(along=(0.25, 0.5)).to_dict()["along"] == [0.25, 0.5]`.
- [x] `_make_default_label_styles()["Line"].along == 0.5`; other kinds `None`.
- [x] A serialized line label's style has no `along`; a label with
      `rotation=45` keeps `style["rotation"] == 45`.
- [x] `_serialize_line` of an infinite line emits the resolved length — update
      `test_serializer.py::test_line`,
      `test_serializer.py::test_style_mutates_default_line_length`,
      `test_node_serialization.py::test_infinite_line_has_zero_content_length`.
- [x] `resolve_line_length(Line.from_points(a,b)) == |b-a|`;
      `resolve_line_length(Line(origin, dir)) == 20.0`;
      with `styles_map["Line"].length = 50` → 50.0;
      with `props={"style": LineStyle(length=7)}` → 7.0.
