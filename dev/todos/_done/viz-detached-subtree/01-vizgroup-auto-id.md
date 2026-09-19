# Phase 1 — Centralized id generation + optional node ids

## Goal

A single `generate_id()` helper and optional `id=` on the scene-graph node
classes, so orphan nodes (`VizGroup`, `VizSceneObject`, and for consistency
`VizOverlayObject`/`VizImage`) can be constructed without hand-rolled ids.

## Files

- New: `py/pytanga/viz/_ids.py`
- Edit: `py/pytanga/viz/_nodes.py`
- Edit: `py/pytanga/viz/scene.py`
- Edit: `py/tests/viz/test_nodes.py`

## Steps

- [x] **1.1 — `_ids.py` with `generate_id()`**
  - `generate_id() -> str` returning `uuid4().hex[:8]`; module docstring noting
    it is the single id convention shared by `_nodes.py` and `scene.py`.

- [x] **1.2 — Use `generate_id()` in `scene.py`**
  - Import `generate_id` in `scene.py`; replace the body of the existing
    `_generate_id()` (line ~946) with `return generate_id()` so the existing
    `from .scene import _generate_id` call sites keep working.

- [x] **1.3 — Optional `id=` on `VizSceneObject`**
  - Change `__init__(self, id: str | None = None, entity, style=None, *, ...)`
    and pass `id or generate_id()` to `VizNode.__init__`.  Update the docstring.

- [x] **1.4 — Optional `id=` on `VizGroup`**
  - `__init__(self, id: str | None = None, *, name="", transform=None,
    visible=True)` → `super().__init__(id or generate_id(), None, None,
    kind="VizGroup", ...)`.

- [x] **1.5 — Optional `id=` on `VizOverlayObject` / `VizImage` (consistency)**
  - Apply the same `id: str | None = None` defaulting so every node kind can be
    constructed detached.

- [x] **1.6 — Tests**
  - `VizGroup()` and `VizSceneObject(None, Point(...))` yield a non-empty `id`;
    two defaulted nodes get distinct ids; an explicit `id=` is preserved.

## Validation

`uv run pytest py/tests/viz/test_nodes.py -q && uv run ruff check py/pytanga/viz/_ids.py py/pytanga/viz/_nodes.py py/pytanga/viz/scene.py py/tests/viz/test_nodes.py`

## Notes

- Keep `_nodes.py` importing only `_ids` (never `scene.py`) to avoid the
  existing `scene.py ↔ _nodes.py` circular import.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture. If this
work introduces or changes architecture, update the developer docs.
