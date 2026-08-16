# Phase 10 — Example script demonstrating `VizGroup` + transforms

**Status:** Done

## Goal

Add a runnable example under `py/examples/viz/` that demonstrates:
- creating a `VizGroup` via `viz.add_group(...)`,
- attaching entities to the group via the group reference (`grp.new(...)`),
- animating a scene using direct transforms on both groups and individual
  elements (`translate`, `rotate`, `transform(...)` with `Rotor`/`Motor`/…),
  and
- the transform-only flush path (no per-frame vertex recomputation).

## Files

- New: `py/examples/viz/demo_scene_graph.py`

## Script outline

- [x] Header/docstring explaining what it demonstrates and how to run it
      (`uv run python py/examples/viz/demo_scene_graph.py`).
- [x] Build a compound object:
  - [x] `grp = viz.add_group("spinner")`
  - [x] `grp.new(Point(...), style=...)` (or a small set of `Point`/`Line`).
- [x] Add some independent elements to the main scene for contrast.
- [x] Animate in a loop:
  - [x] `grp.rotate(axis=(0,0,1), angle=step)` → group-only `transform` aspect.
  - [x] `element.translate(x=..., y=...)` (element-local transform).
  - [x] Use `grp.transform(Rotor(...))` and/or `Motor(...)` / `Translator(...)`
        to showcase the operator-based transform API.
- [x] `viz.flush()` in the loop to push transform-only aspect updates.
- [x] Keep it lightweight and idiomatic; follow the style of existing
      `py/examples/viz/demo_animation_*.py` scripts (signal handling,
      `viz.run()` / `viz.start()` conventions).

## Verification

- [x] `uv run python py/examples/viz/demo_scene_graph.py` runs without error.
- [x] The group rotates as a unit; individual elements translate independently.
- [x] No full entity re-serialization is emitted for transform-only changes
      (verify by watching the server log / WS messages — only `transform`
      aspect patches).
- [x] `uv run ruff check py/examples/viz/demo_scene_graph.py` passes.