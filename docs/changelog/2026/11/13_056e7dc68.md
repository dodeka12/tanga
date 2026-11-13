# Changes since version 2.27.0

## New Features

- **ActPolygon vertex tags & selection** — per-vertex string tags with a
  deterministic tag→color palette, a settable selected vertex with a custom
  marker style, and backend-side click selection.  Tags, selection, and segment
  colors are keyed by a stable vertex identity so they survive insert/delete
  edits.
- **Per-segment path colors** — `PointPath.segment_colors` and
  `ActPolygon.segment_colors` keyed by stable vertex identity; explicit segment
  colors override per-point colors and serialize as `segmentColors` for in-place
  Three.js updates without tinting explicit vertex colors.
- **LabelMe tags & segment colors** — labelme JSON round-trips `vertex_tags`
  and `segment_colors` as custom shape keys, with `LabelMeLoadResult.warnings`
  for malformed metadata and a new `iter_shapes` accessor.
- **Tagged labeling example** — `calibrated_labeling_app.py` tags the selected
  vertex with `1`/`2` (default `1`), colors tag `2` magenta, and derives magenta
  segment ranges on the backend; `image_labeling_app.py` gains tagging controls
  and tag/segment-color save/load.
