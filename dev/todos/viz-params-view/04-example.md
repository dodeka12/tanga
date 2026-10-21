# Phase 4 — Example: dict, dataclass (`param_ui`), and raw `field()`

> **Architecture note — check the developer docs.** Before implementing, check
> `dev/workflows/example-docs.md` (description + `Keywords:` header).  This phase
> only adds an example; no architecture change.

## Goal

Add a runnable example that demonstrates `ParamsView` three ways: a plain `dict`
with a `styles` dict, a `@dataclass` using the `param_ui()` helper, and a
`@dataclass` using raw `dataclasses.field(metadata={"param_ui": ...})`.

## Files

- **New** `py/examples/viz/ui/controls/params_view.py`.
- **Generated** `docs/py/examples/viz/ui/controls/params_view.md` (+ index pages) via the docs tool.

## Steps

- [x] **4.1 — example script**
  - `params_view.py` with the standard header (license + docstring: one-line
    `params_view.py — …`, longer explanation, `Run with:`, `Keywords:`).
  - Scene: a sphere (`entity_id="sphere"`) + a `SplitView("horizontal", …)` with a
    left `GroupView` (or bare `ParamsView`) and a right `SceneView("")`.
  - Show three `ParamsView` instances:
    1. dict mode — `ParamsView({"radius": 2.0, "wireframe": False}, styles={"radius":
       SliderUI(title="Radius", min=0.1, max=5.0)})`;
    2. dataclass via `param_ui()` — `@dataclass` with `field`-defaults written with
       `param_ui(…, ui=SliderUI(…))`, `CheckboxUI`, `ColorPickerUI`, `DropdownUI`;
    3. dataclass via raw `field()` — one field shown as
       `field(default=2.0, metadata={"param_ui": SliderUI(title="Radius", min=0.1,
       max=5.0)})` to document the helper-free alternative.
  - A single `on_change` handler updates the sphere from the changed dict/dataclass
    and calls `viz.flush()`.
- [x] **4.2 — docs**
  - Run `uv run python tools/generate-example-docs.py` then `--check`.

## Validation

```bash
uv run ruff check py/examples/viz/ui/controls/params_view.py && uv run python tools/generate-example-docs.py --check
```
