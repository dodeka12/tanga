# Phase 8 — Docs, example docs, changelog, full validation

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Document the new API and the tagged-labeling workflow, regenerate the example
docs, add the branch changelog, and run the full validation gate.

## Files

- Edit: `docs/py/viz/entities/active-elements/act-polygon.md`
- Edit: `docs/py/viz/entities/point-path.md`
- Edit: `docs/py/viz/entities/labelme.md`
- Edit: `py/examples/apps/calibrated_labeling_app.py` docstring
- Edit: `py/examples/apps/image_labeling_app.py` docstring
- Generated: `docs/py/examples/apps/calibrated_labeling_app.md`,
  `docs/py/examples/apps/image_labeling_app.md`
- New: `docs/changelog/2026/11/13_viz-act-polygon-vertex-tags.md`

## Steps

- [x] **8.1 — `act-polygon.md`**
  - Add a "Vertex tags and selection" section documenting:
    - `vertex_tags`, `set_vertex_tag(s)`, `default_vertex_tag`, `tagging`,
      `set_tag_color`, and the deterministic `TAG_PALETTE` fallback;
    - `selected_vertex`, `set_selected_vertex`,
      `selected_handle_style`, `select_on_click`, `on_vertex_click`;
    - the handle-style precedence (base → tag color → selected style);
    - stable vertex identity and remapping on insert/prepend/delete/fuse.
  - Add a "Segment colors" section documenting `segment_count`,
    `segment_colors`, `set_segment_colors`, `set_segment_color`, and
    `clear_segment_color`, including the closed-polygon closing segment.
  - Add a short code example that tags vertices, selects one, and colors a
    segment.

- [x] **8.2 — `point-path.md`**
  - Document `segment_colors`, `set_segment_color(s)`, the precedence over
    per-point colors, and the `segmentColors` JSON key.
  - Note that a `None` segment color falls back to the per-point colors.

- [x] **8.3 — `labelme.md`**
  - Document the two custom shape keys `vertex_tags` and `segment_colors`, the
    omit-when-empty rule, and the canonical-vertex alignment (closing duplicate
    dropped).
  - Document `LabelMeLoadResult.warnings`, `iter_shapes`, and 2-/3-tuple
    `shapes_from_objects`.

- [x] **8.4 — Example docs**
  - Update the `calibrated_labeling_app.py` module docstring with the tagging
    workflow (click a vertex, press `1`/`2`, default `1`, tag `2` magenta,
    magenta segment ranges) and add `tagging`, `keyboard`, `segment colors` to
    its `Keywords:` header.
  - Update the `image_labeling_app.py` docstring and `Keywords:` header for the
    new tagging controls.
  - Run `uv run python tools/generate-example-docs.py` to regenerate both
    example pages; then run `--check`.

- [x] **8.5 — Changelog**
  - Create `docs/changelog/2026/11/13_viz-act-polygon-vertex-tags.md` (filename
    uses the branch name, per `dev/workflows/changelog.md`).
  - Title: `# Changes since version 2.27.0` — confirm the value with
    `uv run python tools/last-release.py` at implementation time and use its
    exact output.
  - Add a `## New Features` section with self-contained bullets:
    - **ActPolygon vertex tags & selection** — per-vertex string tags with a
      deterministic tag→color palette, a settable selected vertex with a custom
      style, and backend-side click selection.
    - **Per-segment path colors** — `PointPath.segment_colors` and
      `ActPolygon.segment_colors` keyed by stable vertex identity; explicit
      segment colors override per-point colors and serialize as `segmentColors`
      for in-place Three.js updates.
    - **LabelMe tags & segment colors** — labelme JSON round-trips
      `vertex_tags` and `segment_colors` as custom shape keys, with
      `iter_shapes` and warnings for malformed metadata.
    - **Tagged labeling example** — `calibrated_labeling_app.py` tags the
      selected vertex with `1`/`2` (default `1`), colors tag `2` magenta, and
      derives magenta segment ranges on the backend.
  - Leave `docs/changelog/index.md` unchanged; the PR workflow adds the entry
    when the changelog is renamed to its hash-based filename.

- [x] **8.6 — Full validation**
  - `uv run pytest -q`
  - `uv run ruff check .`
  - `uv run ty check`
  - `npm --prefix js/dev test`
  - `npm --prefix js/dev run check`
  - `uv run python tools/build-viewer-js.py --check`
  - `uv run python tools/generate-example-docs.py --check`
  - `uv run mkdocs build --strict`

## Validation

`uv run pytest -q && uv run ruff check . && uv run ty check && npm --prefix js/dev test && npm --prefix js/dev run check && uv run python tools/build-viewer-js.py --check && uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict`

## Notes

- Follow `dev/workflows/changelog.md` for the title and filename, and
  `dev/workflows/pull-request.md` for the later hash rename.
- `mkdocs build --strict` requires the generated example docs to be current.
- If the plan changed any documented architectural contract, update the
  relevant `docs/dev/architecture/` page as part of this phase.
