# Phase 4 — Example + example docs

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Ship a runnable example that demonstrates all six requests at once, following
`dev/workflows/example-docs.md` (description docstring + `Keywords:` header) and
regenerating the example gallery.

## Files

- New: `py/examples/viz/ui/controls/tooltips.py`
- Generated: `docs/py/examples/**` (via `tools/generate-example-docs.py`)

## Steps

- [x] **4.1 — `tooltips.py`**
  - Layout: `SplitView(orientation="horizontal")` with a control
    `GroupView(tooltip=…)` on the left and a `SceneView` pane with a sphere on
    the right (mirror the structure of
    `py/examples/viz/ui/controls/hide_sphere.py`).
  - Controls inside the group:
    - `SliderView("radius", tooltip="Radius of the sphere in model units")`,
    - `ButtonView("explain", "Explain", icon="material:help",
      icon_only=True, tooltip="Explain the current setup")` (icon-only →
      `aria-label` + switch-aware hover fallback),
    - `CheckboxView("show_tooltips", "Show tooltips", value=True)` wired to
      `viz.set_tooltips_enabled(bool(value))` — the app-level switch from
      request #2,
    - `ButtonView("retitle", "Rewrite tooltip")` that calls
      `viz.set_control_tooltip("radius", f"Radius = {value:.2f}")` with the
      current value — the runtime update from request #1.
  - A `MenuView("Help", children=[…], tooltip="Help topics")` in the scene
    overlay (or the group) to show request #6.
  - Handlers are `async def … (value, event)` like the other examples; call
    `viz.flush()` where entity values change.
  - Docstring: one paragraph description, `Run with:  uv run python …`, and a
    `Keywords:` line (tooltip, tooltips, help, group, button, menu, checkbox).

- [x] **4.2 — Regenerate example docs**
  - `uv run python tools/generate-example-docs.py` and commit the regenerated
    `docs/py/examples/**` output (nav/JSON included) with the example.

## Validation

```bash
uv run python -c "import ast; ast.parse(open('py/examples/viz/ui/controls/tooltips.py').read())" \
  && uv run python tools/generate-example-docs.py && git status --short docs/py/examples | head
```

## Notes

- Examples import from the installed `pytanga` package (see the other examples);
  do not run the GUI in CI.
- Keep the example dependency-free beyond `pytanga.viz` / `pytanga.geometry`
  so the docs build stays fast.
