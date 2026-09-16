# Viz Detached Subtree & Operator-Analysis Hint — Overview

**Created:** 2026-09-15 | **Status:** Done | **Branch:** `feat/viz-detached-subtree`

## Goal

Let scene-agnostic "composed object" classes (e.g. `CylinderMass` /
`ComposedMass`) build a complete scene-graph subtree — a `VizGroup` plus
`VizSceneObject` children carrying partially- or fully-specified styles
(including texture labels) — **before** any `Visualizer`/`Scene` exists, and
then insert that subtree into a scene as if each part had been added through
`viz.add(...)`: every descendant gets a stable id, is registered in the scene,
has its partial style backfilled from the scene's per-kind defaults, and stays
individually addressable (update / restyle / remove / interact).  Companion
(from the same `_input` doc): an `expect=` hint on `analyze_operator` so a
half-turn reflection — a line in 3D, a point in 2D — can be coerced to a
`Rotor` or `GeneralRotor`, which every downstream matrix/transform path
understands.

## Architecture (short)

- **`_ids.py`** (new): single `generate_id()` (`uuid4().hex[:8]`); used by both
  `_nodes.py` (node id defaults) and `scene.py`.
- **`_nodes.py`**: `VizGroup` / `VizSceneObject` (and overlay/image for
  consistency) accept `id=None` → `generate_id()`.
- **`scene.py`**: new `Scene.add_subtree(root)` DFS-registers every descendant
  into `_nodes`, backfilling each node's partial style from the scene's
  per-kind defaults; the `add_viz` `VizGroup` branch calls it; `update` and
  `update_entity` become node-first (fall back to `_nodes`).
- **`analysis.py` / `_geometry.py`**: `expect=` keyword on `analyze_operator`,
  `analyze`, `Geometry.which_operator`, `Geometry.analyze`.

## Canonical contract (fixed up front)

### 1. Auto-generated node ids

```python
class VizGroup(VizSceneObject):
    def __init__(self, id: str | None = None, *, name="", transform=None, visible=True):
        super().__init__(id or generate_id(), None, None, kind="VizGroup", ...)

class VizSceneObject(VizNode):
    def __init__(self, id: str | None = None, entity=None, style=None, *, ...):
        super().__init__(id or generate_id(), ...)
```

`generate_id()` == `uuid4().hex[:8]`, identical to the existing
`Scene._generate_id`.

### 2. `Scene.add_subtree`

```python
def add_subtree(self, root: VizSceneObject, *, object_id: str | None = None) -> str:
    """Register *root* and every scene-layer descendant; return the root id."""
```

- DFS pre-order with a visited set.
- `node.id = node.id or generate_id()`.
- Register each scene node in `_nodes[id]`; raise `ValueError` if `id` already
  maps to a **different** node.
- Only the root is appended to `_order` (descendants are reached via
  `parent.children` in `_dfs_preorder`).
- Partial styles are backfilled: each descendant's `style` is resolved against
  the scene's per-kind defaults (`_style_to_output(..., styles_map=
  self.styles.kind)`), mirroring `_make_scene_node` (including top-level
  `color`/`opacity`), so the subtree renders exactly as if its parts had been
  added individually.

### 3. Node-first `update` / `update_entity`

`Scene.update(object_id, **properties)` and `Scene.update_entity(object_id,
entity)` look up `_nodes` when `object_id` is not in `_objects`, operating on
the `VizSceneObject` directly (`apply_props` / `set_entity`).  Behaviour for
ids present in `_objects` is unchanged.

### 4. Operator `expect=` hint

```python
def analyze_operator(mv: MV, *, expect: type[Operator] | tuple[type[Operator], ...] | None = None) -> Operator | None: ...
```

- Classify as today; then, if `expect` is given and the result is not an
  instance of `expect` but has a lossless reinterpretation, return the coerced
  operator.  Coercion is **dimension-aware**: only "reflection in a
  codimension-2 subspace" is a half-turn.
- Coercion rules:
  - 3D `ReflectionLine` → `Rotor(angle=π, axis=line.direction)` for
    `expect=Rotor` (only when the line passes through the origin); →
    `GeneralRotor(angle=π, axis=line.direction, origin=line.origin)` for
    `expect=GeneralRotor`.
  - 2D `ReflectionPoint` → `Rotor(angle=π, axis=Direction(0,0,1))` for
    `expect=Rotor` (only when the point is the origin); →
    `GeneralRotor(angle=π, axis=Direction(0,0,1), origin=point)` for
    `expect=GeneralRotor`.
  - `ReflectionPlane`, 3D `ReflectionPoint`, and 2D `ReflectionLine` are
    improper and never coerce.
- `expect` never suppresses a legitimate different classification: when no
  lossless reinterpretation matches, return the natural result (or `None`).

## Decisions (confirmed)

- Detached subtrees may carry **partial** styles; `add_subtree` backfills them
  from the scene's per-kind defaults (exactly like `viz.add`), so composed
  objects don't need a fully-resolved style up front.
- Descendants are registered in `_nodes` only — not `_order` — to avoid them
  appearing as extra roots in `_dfs_preorder`.
- `expect=` coerces half-turn reflections (3D `ReflectionLine`, 2D
  `ReflectionPoint`) to a `Rotor` or `GeneralRotor`; the mechanism is generic
  for future rules.
- Id generation is centralized in `_ids.py`; `scene._generate_id` keeps working.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-vizgroup-auto-id.md](./01-vizgroup-auto-id.md) | `_ids.py` + optional `id=` on node classes |
| 2 | [02-scene-register-subtree.md](./02-scene-register-subtree.md) | `Scene.add_subtree` (register + style backfill) + node-first update |
| 3 | [03-add-viz-group-branch.md](./03-add-viz-group-branch.md) | Wire `add_viz` `VizGroup` branch to `add_subtree` + integration tests |
| 4 | [04-example-script.md](./04-example-script.md) | Example script: composed object built detached, inserted later |
| 5 | [05-documentation.md](./05-documentation.md) | New user doc on composing detached scene subtrees |
| 6 | [06-operator-analysis-expect-hint.md](./06-operator-analysis-expect-hint.md) | `expect=` hint for `analyze_operator` / `Geometry.analyze` |
| 7 | [07-docs-changelog.md](./07-docs-changelog.md) | Developer docs + branch changelog + full validation |

## Testing as you go

- Python (nodes/scene): `uv run pytest py/tests/viz/test_nodes.py -q`
- Python (geometry): `uv run pytest py/tests/geometry/test_typed_analyzers.py py/tests/geometry/test_geometry_e3_analysis.py py/tests/geometry/test_geometry_n2_analysis.py py/tests/geometry/test_geometry_pga2_analysis.py -q`
- Lint: `uv run ruff check py/pytanga/viz/_nodes.py py/pytanga/viz/scene.py py/pytanga/geometry/analysis.py py/pytanga/geometry/_geometry.py`
- Example docs: `uv run python tools/generate-example-docs.py --check`
- Docs: `uv run mkdocs build --strict`

## Non-goals

- No automatic per-child labels during subtree insertion.
- No frontend/JS changes.
- No `expect` reinterpretations beyond the reflection → `Rotor`/`GeneralRotor`
  half-turn rules above.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture. If this
work introduces or changes architecture, update the developer docs.
