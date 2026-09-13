# Changes since version 2.3.0 (2.4.0-rc1)

## New Features
- **Q3 point tuples** — OPNS point joins (grades 2–7) now analyze to a
  `PointSet` via the quadric complement: `_analyze_q3` dualizes IPNS → OPNS so
  every IPNS grade routes through a single dispatch path,
  `intersect_three_quadrics` locates `Q3 = 0` along the quartic `Q1 ∩ Q2`
  (exact plane-pair member, or a Newton-refined cone member), and
  `pointset_from_blade` filters the candidates to the points lying on *all*
  complement quadrics; a grade-7 join yields its eight base points
  (Cayley–Bacharach).
- **`point_tuples_demo.py`** — visualizes 1–7 point tuples in distinct colors,
  each translated into its own quadrant of a 5×5×5 cube.
- **Developer docs** — `quadric-module.md` architecture page and
  `conic-quadric-space.md` GA math page, plus a `dev/theory` note on the
  point-tuple dual/net correspondence.  The type-hint work adds
  `typing-and-annotations.md` (the annotation policy: annotate everything,
  avoid `Any`, prefer proving over casting, and how the `ty` + ruff `ANN` gates
  are wired) and a **Handler types** section in
  `viz-controls-and-interactions.md` documenting every handler alias
  (`ControlHandler`, `EnumOptionsHandler`, `InteractionHandler`,
  `ActHandler`/`ActEventHandler`/`ActClickHandler`), the `ControlEvent` →
  `InteractionEvent` → `ClickEvent`/`DragEvent`/`ScrollEvent` event hierarchy,
  and how each family registers in the shared `(id, event)` registry.

## Breaking Changes
- **`pytanga.viz.Handler` removed** — the name ambiguously resolved to the
  1-arg interaction handler while the `on_*` control fields are typed with the
  2-arg shape; use the new `ControlHandler` (`(value, event)`) or
  `InteractionHandler` (`(event)`) alias instead.
- **Interaction API typed instead of `Any`** — `on_interaction(...)` now
  declares `event_type: InteractionEventType` / `handler: InteractionHandler`
  and `set_interaction(...)` declares `config: InteractionConfig` on
  `Visualizer`, `VizSceneHandle`, `VizObjectRef`, `InteractionHost` and
  `Scene`.  The runtime contract is unchanged (`event_type.value` already
  required an enum member), but code passing loose values no longer
  type-checks.

## Bug Fixes
- **Quartic intersection sampled too sparsely** — `intersect_quadrics` shadowed
  its sampling count with the cone's negative-inertia count, so the cone was
  sampled with `n = 1`; the cone is now sampled at the requested density.
- **Point-set labels stuck at the origin** — `PointSet` now anchors its label at
  the centroid of its points instead of the world origin.
- **Point tuples not renderable** — `PointSet` was missing from the geometry
  `Entity` union, so the viewer failed to resolve it; added.
- **`ReflectionPlane` label frame raised `AttributeError`** — the label frame
  read `entity.normal`, which a `ReflectionPlane` does not have (it exposes the
  wrapped `plane`), so labelling a plane-reflection operator failed; it now
  reads `entity.plane.normal`.

## Refactor
- **Dev notes moved under `dev/theory`** — the quadric plane-pair and rotor
  derivations moved from `dev/notes` to `dev/theory`, and the release-notes file
  was renamed to the `2.4.0-rcX` series.
- **One `ControlEvent` class** — `pytanga.viz._interaction` declared a second
  class of that name for its events; the interaction events (now sharing the
  new `InteractionEvent` base, which carries `object_id`, `event_type` and
  `camera`) derive from the public `pytanga.viz.ControlEvent`, so the package
  has a single event hierarchy.
- **Explicit handler aliases** — `ControlHandler` and `InteractionHandler`
  replace the ambiguous `Handler`; the shared `(id, event)` registry types both
  families and exposes `get_interaction()` alongside `get()`.
- **Type-hint coverage + `ty` enforcement** — `py/pytanga` and `py/examples`
  are fully type-annotated (644 untyped definitions) and both gates are now
  permanent: `ruff` carries the `ANN` coverage rules from `pyproject.toml`
  (`ANN401` relaxed for the dynamically-typed binding/registry surfaces) and
  `ty` runs as a gating pre-commit hook and CI job.  Triage of the 584
  baseline `ty` diagnostics fixed real bugs (see above) and corrected several
  annotations: `Geometry.__call__`, `Visualizer.add` and `MVTensor.__getitem__`
  are now overloaded, view/control
  enums accept their string values (`direction="horizontal"`,
  `position="bottom-right"`, `product="op"`), `Scene.add`/`update_entity`
  accept the full viz entity union, and sequence-typed inputs
  (`to_tensor`, `product_matrix`, `MVTensor.masks`, `PointPath.default_colors`)
  take `Sequence[...]` so `list[MV]` is accepted despite invariance.
  Deliberate suppressions, all verified false positives:
  `blade_mask/_dispatch.py` (`unsound-return-statement` — the binding is
  resolved by name via `getattr`) and the three `globals().update()`
  blade-name lines in `ga/basis/basis_usage.py`
  (`unresolved-reference`).  The `py/tests` suite is deferred from the
  coverage gate and keeps its star-import lint debt; the standing policy for
  all new code lives in `docs/dev/architecture/typing-and-annotations.md`.
- **One-time `ruff format` sync** — `pre-commit run --all-files` surfaced 51
  already-drifted files (mostly under `py/tests`), so the repository now matches
  its own `ruff-format` hook; the change is whitespace/line-splitting only.
