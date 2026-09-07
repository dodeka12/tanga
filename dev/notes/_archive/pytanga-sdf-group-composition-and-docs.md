# Feature request: allow `SdfGroup`/`SdfObject` as `VizGroup` members and construct `Transform` from a GA operator

**Status:** proposed upstream (not a wafer-grinding task) — kept here for reference.


## Summary

`pytanga.viz.sdf` (`SdfObject`, `Composed`, `SdfGroup`, CSG operators, primitive
library) is a working, documented, composable-SDF rendering subsystem — see
`.dep-docs/pytanga/py/viz/sdf/` and the runnable examples in
`.dep-examples/pytanga/viz/sdf/*.py`. Three real gaps remain:

1. **`SdfGroup`/`SdfObject`/`Composed` cannot be added as a child of a
   mesh-based `VizGroup`, nor via the main `Visualizer.add()`/`.new()` at
   all.** Mesh-based scene composition
   (`Visualizer.new(some_mass_object.visual_geometry())`, where
   `visual_geometry()` returns a `pytanga.viz.VizGroup`) has no way to include
   a ray-marched SDF element as one of its children, nor to add one directly
   to the main `Visualizer`'s scene — only the separate, standalone
   `pytanga.viz.sdf.SdfVisualizer` can render `SdfGroup`/`SdfObject`/`Composed`
   today. This blocks mixing a ray-marched composite solid with regular mesh
   decorations (e.g. thin wireframe spokes, labels, arrows) under one shared
   transform node/viewer.

   The upstream docs (`.dep-docs/pytanga/py/viz/sdf/sdf-objects.md`) already
   describe *exactly* this feature — an `SdfStyle` marker style plus
   `SdfObject`/`Composed`/`SdfGroup` accepted directly by the main
   `Visualizer.add()`/`.new()`, via `viz.add(entity, style=SdfStyle(...))` —
   but it is **not yet in any released `tanga-py` version**: `SdfStyle` does
   not exist anywhere in the installed `tanga-py==1.17.0` package
   (`pytanga/viz/__init__.py`, `pytanga/viz/visualizer.py`, and
   `pytanga/viz/_scene_objects.py` have zero references to it), and `1.17.0`
   is also the latest version published on PyPI. So this item is really:
   *please publish a `tanga-py` release that includes the already-documented
   unified SDF object model* — not a request to design a new feature from
   scratch. `VizGroup` mixing (adding an `SdfObject`/`SdfGroup` as a *child
   node* of an existing mesh `VizGroup`, rather than only as a top-level
   `viz.add()`/`viz.new()` call) is not explicitly covered by
   `sdf-objects.md` either, so that part may still need to be raised
   separately once the base feature ships.

2. **`pytanga.viz._nodes.Transform` cannot be constructed directly from a GA
   operator.** `Transform` (the TRS node every `VizGroup`/`VizSceneObject`
   uses for its own `transform=`) only exposes `set_matrix()`/`from_matrix()`
   (a raw 4x4 numpy matrix) and incremental `translate()`/`rotate()`/
   `scale_by()`/`apply_matrix()` calls — there is no way to build one
   directly from a `pytanga.geometry` operator (`Motor`, `Rotor`,
   `GeneralRotor`, `Dilator`, `Translator`), even though `_T.operator_to_matrix`
   (used internally by `VizSceneObject.apply_transform()`) already knows how
   to convert exactly these operator types to a 4x4 matrix. Also, `Transform`
   is not part of pytanga's public API (not re-exported from
   `pytanga.viz.__init__.py`), so callers who do need one (e.g. to bake a
   body's static placement into a `VizGroup` at construction time, rather
   than applying it as a follow-up `apply_transform()` call) must import the
   private `pytanga.viz._nodes` module directly.

3. **No smooth-blending (smooth-CSG) parameter for SDF objects in the
   standard visualizer.** The CSG operators documented for the standard
   viewer's unified object model (`SdfObject`/`Combine`/`Composed`/`SdfGroup`
   — `+`/`-`/`&`/`^` and the `(obj, mode)`/`ECompose` forms, see
   `sdf-objects.md`) are all *hard* combinators (`min`/`max`), with no
   equivalent of a `smoothness` knob for rounded, blended joins between
   members. `.dep-docs/pytanga/py/viz/sdf/sdf-viewer.md` documents
   `smooth_union`/`smooth_intersection`/`smooth_subtract` with a per-object
   `smoothness` knob, but only for the separate, standalone `SdfVisualizer`
   path (`viz.add(..., combine="smooth_union", smoothness=...)`) — and even
   there, it isn't actually present in the installed `tanga-py==1.17.0`
   (`primitives.py` has no smooth-combinator code at all, confirmed by
   searching the installed package source). So this is a genuine gap in both
   paths, but the immediate ask is for the standard visualizer specifically:
   a `smoothness`/`blend` field on `SdfStyle`/`Combine`/`Composed`/`SdfGroup`
   (or an equivalent `smooth_union`/`smooth_intersection`/`smooth_subtract`
   combine mode) so members can be joined with rounded fillets instead of a
   hard seam.

## Why this matters (wafer-grinding use case)

We're evaluating whether `MassObject` subclasses (`CylinderMass`,
`ComposedMass`, future shapes) should each expose a composable SDF element
alongside (or instead of) today's `VizGroup`-returning `visual_geometry()`, so
that `ComposedMass` can render its constituents as one true ray-marched union
(with real CSG, smooth blending, and shared shadowing) instead of several
independently-drawn `VizGroup`s that merely depth-sort against each other.

This composes naturally at exactly two levels that map onto our existing
local/world frame split (`FrameTransform`/`local_to_world` in
`MassObject`/`ComposedMass`):

- A `ComposedMass` built from several `CylinderMass`-like leaves wants to fold
  each leaf's own SDF element into one `SdfGroup`, positioning each member via
  `SdfGroup.set_member_transform()` — this already works today, but joins
  between members are always a hard seam (gap 3 above) — a rounded, blended
  join at contact surfaces (e.g. a shaft meeting a hub) needs a smoothness
  parameter that doesn't exist yet in the standard visualizer's CSG model.
- Any assembly that also wants a few plain mesh decorations (spoke lines,
  arrows, labels) alongside its ray-marched solid, all reachable through one
  `VizObjectRef` for uniform transform updates — this does **not** work today
  (gap 1 above), since `visual_geometry()`'s contract is "returns one
  `VizGroup`", and the main `Visualizer`/`VizGroup` has no knowledge of SDF
  elements at all in the currently-released `tanga-py`. Until the
  documented-but-unreleased unified object model ships, an assembly wanting
  both would need two separate viewers/scenes (one `Visualizer` for meshes,
  one `SdfVisualizer` for the ray-marched parts).

Separately, `MassObject.visual_geometry()` (`CylinderMass`'s implementation,
specifically) needs to bake a body's static local-to-world placement into its
returned `VizGroup`'s own `transform=` at construction time (rather than
requiring every caller to follow up with an `apply_transform()` call), so
that a detached `VizGroup` is already correctly placed in the world frame the
moment it's added to a scene. `FrameTransform` computes this placement as a
rotor + translation vector (`local_to_world`, a GA motor/versor) — the same
kind of operator `apply_transform()` already accepts — but has no direct path
to a `Transform` object from it; see "Workaround" below.

## Requested changes (upstream, in `tanga-py`)

1. **Publish a `tanga-py` release containing the already-documented unified
   SDF object model** (`SdfStyle`, `SdfObject`/`Composed`/`SdfGroup` accepted
   by the main `Visualizer.add()`/`.new()`), and additionally **allow
   `SdfGroup`/`Composed`/`SdfObject` as a `VizGroup` child**, so a `VizGroup`
   can mix mesh scene nodes and one (or more) ray-marched SDF scene nodes
   under a single group transform, e.g.:

   ```python
   group = VizGroup(id="cylinder")
   group.add_child(sdf_group)  # ray-marched solid
   group.add_child(spoke_line_a)  # plain mesh Line entity
   group.add_child(spoke_line_b)
   ```

   The base `viz.add(entity, style=SdfStyle(...))` mixing is already fully
   designed per `.dep-docs/pytanga/py/viz/sdf/sdf-objects.md` — this item is
   mainly "please release it" plus the `VizGroup`-child-nesting part
   specifically, which isn't obviously covered by the existing doc.

2. **Add a way to construct `Transform` directly from a GA operator**, e.g.
   a classmethod alongside `from_matrix()`:

   ```python
   Transform.from_operator(op: Translator | Rotor | GeneralRotor | Motor | Dilator) -> Transform
   ```

   (internally just `cls().set_matrix(_T.operator_to_matrix(op))`, reusing
   the conversion `VizSceneObject.apply_transform()` already relies on), and
   export `Transform` from `pytanga.viz.__init__.py` so this — and the
   existing `set_matrix()`/`from_matrix()`/`apply_matrix()` methods — are
   reachable without importing the private `pytanga.viz._nodes` module.

3. **Add a smooth-blending parameter to the standard visualizer's SDF CSG
   model**, e.g. a `smoothness` field on `SdfStyle` (or per-combine, on
   `Combine`/`Composed`/`SdfGroup` members) plus `smooth_union`/
   `smooth_intersection`/`smooth_subtract` combine modes alongside the
   existing hard `union`/`intersection`/`subtract`/`xor`:

   ```python
   SdfGroup(
       sphere(1.0, id="hub"),
       (capped_cylinder(1.5, 0.35, id="shaft"), "smooth_union", 0.15),  # rounded join
   )
   ```

   Mirrors the `smooth_union`/`smooth_intersection`/`smooth_subtract` +
   `smoothness` knob already documented for the standalone `SdfVisualizer` in
   `sdf-viewer.md` — this request asks for the same capability on the
   standard-visualizer object model (`SdfObject`/`Combine`/`Composed`/
   `SdfGroup`), plus actually landing the smooth combinators in
   `primitives.py` (currently missing from both paths in the installed
   `tanga-py==1.17.0`).

## Workaround (used in wafer-grinding, if/until upstream lands this)

None implemented yet for the SDF/mesh mixing request (1) — filed directly
after an exploratory investigation (no code changes made). If we need
SDF+mesh mixing before upstream releases the unified object model, the
fallback is two separate viewers/scenes (a mesh `Visualizer` plus a
standalone `SdfVisualizer`) rather than one combined scene graph.

For request 2 (`Transform.from_operator()`), we've implemented the manual
equivalent in `wafer_grinding`: `FrameTransform` (in
`src/wafer_grinding/frame_transform.py`) computes an explicit 3x3 rotation
matrix from its fitted rotor (sandwiching each world basis vector,
`rotor.vp(e_i)`) plus its translation vector, assembles a 4x4 homogeneous
matrix by hand, and calls `Transform().set_matrix(matrix)` to get a
`Transform` object (`FrameTransform.local_to_world_transform` /
`MassObject.local_to_world_transform`), which `CylinderMass.visual_geometry()`
then passes as `VizGroup(..., transform=...)`. This works, but duplicates
logic `_T.operator_to_matrix()` already has, and requires importing the
private `pytanga.viz._nodes.Transform` directly.
