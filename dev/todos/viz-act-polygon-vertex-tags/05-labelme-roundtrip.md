# Phase 5 — LabelMe round-trip of tags and segment colors

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Persist per-vertex tags and per-segment colors in labelme JSON as custom shape
keys, expose the parsed `LabelShape` to callers, and report malformed metadata
as warnings without dropping the shape.

## Files

- Edit: `py/pytanga/viz/labelme.py`
- Edit: `py/tests/viz/test_labelme.py`
- Edit: `py/tests/viz/test_calibrated_labeling_example.py` (only if call sites
  need adapting; `iter_objects` stays backwards compatible)

## Steps

- [x] **5.1 — `LabelShape` fields**
  - Add `vertex_tags: list[str | None] | None = None`.
  - Add `segment_colors: list[str | None] | None = None`.
  - Update the class docstring: these are canonical-vertex aligned and are
    never stored on the geometry entity.

- [x] **5.2 — `LabelMeLoadResult.warnings`**
  - Add `warnings: list[str] = field(default_factory=list)` after `errors`.
  - `loads` returns `warnings`; malformed metadata adds a warning and leaves
    the shape in `document.shapes` (unlike `errors`, which skip a shape).

- [x] **5.3 — Parse metadata**
  - Add a helper `_parse_optional_str_list(value, field, count, *,
    closing_duplicate=False)`:
    - `None` → `None`;
    - a non-list or an element that is not `str | None` → warning + `None`;
    - a list of length `count + 1` with `closing_duplicate=True` → drop the
      last entry;
    - a list of length `count` → use it;
    - any other length → warning + `None`.
  - `vertex_tags`: canonical count = number of unique vertices (`len(points)`,
    or `len(points) - 1` when `points[0] == points[-1]`).
  - `segment_colors`: canonical `n` for a closed polygon, `n-1` for a
    linestrip; allow `expected + 1` entries when the closing point is
    duplicated and drop the last entry (the duplicate's zero-length segment).
  - Normalize an all-`None` list to `None` before attaching it, so
    `LabelShape` round-trip equality is stable.
  - Attach the parsed lists to the `LabelShape`.

- [x] **5.4 — Serialize metadata**
  - In `dumps`, emit `"vertex_tags"` and `"segment_colors"` only when the list
    is not `None` and has at least one non-`None` entry.
  - Emit `None` entries as JSON `null`.
  - Place the two keys after `"mask"` and before the ellipse parameters
    (`radius_u`/`radius_v`/`angle`) so the writer order is stable.
  - `loads(dumps(doc))` must round-trip both fields.

- [x] **5.5 — `iter_shapes` and 3-tuple `shapes_from_objects`**
  - Add `iter_shapes(doc) -> tuple[list[tuple[object, LabelShape]], list[str]]`;
    it maps each shape exactly like `iter_objects` but appends `(obj, shape)`.
  - Make `iter_objects` delegate:
    `[(obj, shape.label) for obj, shape in shapes]`.
  - Change `shapes_from_objects` to accept
    `tuple[object, str] | tuple[object, str, Sequence[str | None]]`; the optional
    third element is `vertex_tags`.
  - Extend `_shape_from_object(obj, label, vertex_tags=None)`:
    - for a `PointPath`: detect the closing duplicate, drop the duplicate point
      for `LabelShape.points`, read `obj.segment_colors`, and set
      `LabelShape.vertex_tags` (drop the last tag if `vertex_tags` has the
      duplicate's length); normalize all-`None` `vertex_tags` /
      `segment_colors` to `None`;
    - for other entity types: leave `vertex_tags`/`segment_colors` as `None`.
  - `_entity_from_shape` for `polygon`/`linestrip`: after `_path(...)`, call
    `path.set_segment_colors(shape.segment_colors)` when present.
  - Fix `_path` to append the first point only when `pts[0] != pts[-1]`, so a
    labelme file that already includes the closing point does not gain a second
    zero-length segment.

- [x] **5.6 — Tests**
  - Round-trip a polygon with `vertex_tags` and `segment_colors`; assert both
    survive `dumps`/`loads`.
  - Empty/all-`None` metadata is omitted from the JSON.
  - Malformed metadata (wrong type, wrong length) produces a warning and the
    shape still loads with `None` metadata.
  - `iter_shapes` returns `(entity, LabelShape)`; `iter_objects` still returns
    `(entity, label)`.
  - `shapes_from_objects` accepts 2-tuples and 3-tuples; reads
    `PointPath.segment_colors`; aligns a closing duplicate correctly.
  - `_entity_from_shape` applies segment colors to the resulting `PointPath`.
  - Existing labelme tests and the calibrated example test still pass.

## Validation

`uv run pytest py/tests/viz/test_labelme.py py/tests/viz/test_calibrated_labeling_example.py -q`

## Notes

- `errors` = skipped shapes; `warnings` = loaded shape with ignored metadata.
- Tags live on `LabelShape`, not on `PointPath`; `add_shapes` remains data-only.
- Keep `iter_objects` and 2-tuple `shapes_from_objects` for existing callers.
- The closing duplicate handling applies to both labelme points and tags;
  segment colors already exclude the duplicate because `PointPath` segments are
  `len(points) - 1`.
