# Phase 4 — Example script: composing a detached object

## Goal

A runnable example that builds a multi-part object (e.g. a cylinder + spokes)
as a detached `VizGroup` of `VizSceneObject`s — each with its own style — and
inserts it into a `Visualizer` only at the end.

## Files

- New: `py/examples/viz/scenes/compose_detached.py`
- Regenerate: docs example pages via the generator.

## Steps

- [x] **4.1 — Script skeleton per `dev/workflows/example-docs.md`**
  - License header + module docstring: one-line `<name>.py — …` summary, a
    `Run with:` line, trailing `Keywords:` (e.g. `scene graph, compose, VizGroup,
    detached, cylinder`).

- [x] **4.2 — Build a detached composed object**
  - Construct a `VizGroup` and several `VizSceneObject` children (cylinder +
    a few `Line` spokes) with explicit resolved styles; attach via `add_child`;
    use default `id=` (no hand-rolled ids).

- [x] **4.3 — Insert and render**
  - `viz = Visualizer(...)`; `ref = viz.new(group)`; optionally `ref.translate(...)`
    / `ref.rotate(...)`; `viz.flush()`; `viz.wait()`.

- [x] **4.4 — Regenerate example docs**
  - `uv run python tools/generate-example-docs.py` then `--check`.

## Validation

`uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict`

## Notes

- Check `py/examples/viz/scenes/motor_group_transform.py` and
  `nested_groups.py` first so this example is distinct (it demonstrates the
  *detached-then-insert* flow, not building via `viz.*`).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture. If this
work introduces or changes architecture, update the developer docs.
