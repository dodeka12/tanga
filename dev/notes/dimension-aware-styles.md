# Feature idea: dimension-aware default styles (2D vs 3D)

## Summary

Today the per-kind default styles are one global table
(`_DEFAULT_STYLE_FOR_KIND` → `make_styles()`), shared by 2D and 3D viewers.
`space_dim` lives on `SceneConfig` and only affects the camera/controls and the
default axes/grid choice (`Visualizer._add_default_scene_objects`); it never
changes the per-kind entity styles.

Idea: let the default style for a kind differ between `space_dim == 2` and
`space_dim == 3`, while keeping per-instance `style=` / `color=` overrides
unchanged.

## Proposed seam

- Add `_DEFAULT_STYLE_FOR_KIND_2D` — an overlay dict holding only the kinds that
  should differ in 2D.
- `make_styles(space_dim=3)` / `_make_default_styles(space_dim=3)` start from the
  3D table and overlay the 2D table when `space_dim == 2`.
- `Visualizer._create_scene` (already receives `space_dim`) builds each scene's
  `Scene.styles` with the right dimension.

Because every serialization path already threads the scene's `styles_map`
(`Scene.full_state(styles_map=...)`, `_make_scene_node` → `_style_to_output(...,
styles_map=...)`), the dimension-specific defaults flow through with no further
changes.

## Notes / open questions

- `Visualizer._global_styles` is the user-mutable master; named scenes can
  override `space_dim`, so the 2D overlay must be applied per scene on top of the
  global defaults (do not mutate the master).
- Decide which kinds actually differ (candidate: Ellipse line thickness, Circle
  line thickness, …).
- Deliberately out of scope for `dev/todos/viz-conic-rendering`; track separately.
