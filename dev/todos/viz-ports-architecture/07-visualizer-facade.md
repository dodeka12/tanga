# Phase 7 — `Visualizer` facade + explicit forwarders

## Goal

Shrink `Visualizer` to the facade + composition root; replace `__getattr__` with
explicit thin forwarders so the public API is introspectable.

## Files

- Edit: `py/pytanga/viz/visualizer.py`

## Steps

- [x] **7.1 — Inventory reach-throughs**
  - List every `viz.*` access `VizSceneHandle`/tests still use.
- [x] **7.2 — Explicit forwarders**
  - Replace `__getattr__` with `def`/`@property` forwarders for the public API and
    the `_` internals `VizSceneHandle` needs.
- [x] **7.3 — Remove `__getattr__`**
  - Delete it; confirm `dir(viz)`/`help(viz)` improved.
- [x] **7.4 — Line-count sanity**
  - Record `visualizer.py` line count in the commit.

## Validation

`uv run pytest -q && uv run mkdocs build --strict`
