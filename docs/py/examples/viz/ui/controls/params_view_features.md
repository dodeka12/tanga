# ParamsView: a tour of the advanced features

**Keywords:** params view · controls · param_ui · dataclass · extra_rows · nested · dotted · full_width

One `ParamsView` per panel demonstrates the features added on top of the basic
dict/dataclass → controls mapping:

- **Spec fields** — `unit`, `integer`/`coerce`, `validate`, a
  `(value, label)` dropdown, a `description` tooltip, and a per-field
  `on_change` handler (called instead of the shared handler).
- **Inference** — `Enum` / `Literal` / `Optional[X]` fields infer dropdowns,
  and an `int` field is coerced back to `int` (printed via `event.key` /
  `event.value`).
- **Nested + extra rows** — a dataclass field renders as a nested `GroupView`
  (with its own `extra_rows` button), and `extra_rows` adds a checkbox that
  enables/disables the group, a captioned full-width button (above), and a
  full-width status `MarkdownUI` (below).
- **Runtime API** — buttons call `set_visible` / `set_enabled` / `set_title`
  / `set_options` / `add` / `remove` / `set_state` on a live `ParamsView`;
  nested fields are addressed by dotted key (`set_value("bounds.low", …)`, and
  the shared handler reports a dotted `event.key`).
- **Ergonomics** — `title_from_name=True` (snake_case → "Title Case") and
  `dense=True` (per-view compact density).

## Run

```bash
uv run python py/examples/viz/ui/controls/params_view_features.py
```

## Source

[`viz/ui/controls/params_view_features.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/ui/controls/params_view_features.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""params_view_features.py — ParamsView: a tour of the advanced features.

One ``ParamsView`` per panel demonstrates the features added on top of the basic
dict/dataclass → controls mapping:

- **Spec fields** — ``unit``, ``integer``/``coerce``, ``validate``, a
  ``(value, label)`` dropdown, a ``description`` tooltip, and a per-field
  ``on_change`` handler (called instead of the shared handler).
- **Inference** — ``Enum`` / ``Literal`` / ``Optional[X]`` fields infer dropdowns,
  and an ``int`` field is coerced back to ``int`` (printed via ``event.key`` /
  ``event.value``).
- **Nested + extra rows** — a dataclass field renders as a nested ``GroupView``
  (with its own ``extra_rows`` button), and ``extra_rows`` adds a checkbox that
  enables/disables the group, a captioned full-width button (above), and a
  full-width status ``MarkdownUI`` (below).
- **Runtime API** — buttons call ``set_visible`` / ``set_enabled`` / ``set_title``
  / ``set_options`` / ``add`` / ``remove`` / ``set_state`` on a live ``ParamsView``;
  nested fields are addressed by dotted key (``set_value("bounds.low", …)``, and
  the shared handler reports a dotted ``event.key``).
- **Ergonomics** — ``title_from_name=True`` (snake_case → "Title Case") and
  ``dense=True`` (per-view compact density).

Run with:  uv run python py/examples/viz/ui/controls/params_view_features.py

Keywords: params view, controls, param_ui, dataclass, extra_rows, nested, dotted, full_width
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, Optional

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonUI,
    ButtonView,
    CheckboxUI,
    ControlEvent,
    DropdownUI,
    GroupUI,
    GroupView,
    MarkdownUI,
    ParamsView,
    RowSpec,
    SceneView,
    Size,
    SliderUI,
    SplitView,
    StackView,
    ValueEditUI,
    Visualizer,
    param_ui,
)

viz = Visualizer(reuse_existing=False, title="Tanga — ParamsView features")

viz.add(
    Sphere(Point(0, 0, 0), radius=1.5), entity_id="sphere", color="#4488ff", opacity=0.4
)


def _as_dict(state: Any) -> dict[str, Any]:
    if isinstance(state, dict):
        return state
    return {f.name: getattr(state, f.name) for f in dataclasses.fields(state)}


async def _on_change(state: Any, event: ControlEvent) -> None:
    """Shared handler — prints the changed field and the full state."""
    print(f"  change: {event.key!r} = {event.value!r}  ->  {_as_dict(state)}")


async def _on_radius(value: Any, event: ControlEvent) -> None:
    """Per-field handler — fires for `radius` instead of the shared handler."""
    print(f"  per-field radius: {value} ({type(value).__name__})  key={event.key!r}")


# ── 1. Spec fields (unit / integer / validate / (value, label) / tooltip) ─────
class Unit(Enum):
    MM = "mm"
    CM = "cm"


@dataclass
class SpecParams:
    radius: float = param_ui(
        2.0,
        ui=SliderUI(title="Radius", min=0.1, max=5.0, step=0.05, on_change=_on_radius),
        description="Sphere radius (per-field handler)",
    )
    length: float = param_ui(
        1.5, ui=ValueEditUI(title="Length", min=0.0, max=10.0, unit="m")
    )
    segments: int = param_ui(
        16, ui=ValueEditUI(title="Segments", min=3, max=128, integer=True)
    )
    ratio: float = param_ui(
        0.5,
        ui=SliderUI(
            title="Ratio (0–1)",
            min=0.0,
            max=1.0,
            step=0.05,
            validate=lambda v: 0.0 <= v <= 1.0,
        ),
    )
    unit: Unit = param_ui(
        Unit.MM,
        ui=DropdownUI(
            title="Unit",
            options=[(m.value, m.name.title()) for m in Unit],
        ),
    )


spec_view = ParamsView(
    SpecParams(),
    min_width=Size.px(240),
    on_change=_on_change,
)


# ── 2. Inference (Enum / Literal / Optional / int coercion) ──────────────────
class RenderMode(Enum):
    SOLID = "solid"
    WIRE = "wire"


@dataclass
class InferredParams:
    count: int = 3
    mode: RenderMode = RenderMode.SOLID
    shading: Literal["flat", "smooth"] = "smooth"
    opacity: Optional[float] = 0.5
    wireframe: bool = False


inferred_view = ParamsView(
    InferredParams(),
    min_width=Size.px(240),
    on_change=_on_change,
)


# ── 3. Nested dataclass + extra rows (button above, status below) ────────────
@dataclass
class BoundsParams:
    low: float = 0.1
    high: float = 5.0


@dataclass
class NestedParams:
    bounds: BoundsParams = field(default_factory=BoundsParams)


async def _on_detect(value: Any, event: ControlEvent) -> None:
    print(f"  button: {event.key!r} clicked")


async def _on_reset_bounds(value: Any, event: ControlEvent) -> None:
    # Dotted keys address a field inside the nested group.
    nested_view.set_value("bounds.low", 0.1)
    nested_view.set_value("bounds.high", 5.0)


async def _on_toggle_bounds(value: Any, event: ControlEvent) -> None:
    # A checkbox row disables/enables the nested "bounds" group.
    nested_view.set_enabled("bounds", bool(value))


nested_view = ParamsView(
    NestedParams(),
    min_width=Size.px(240),
    on_change=_on_change,
    styles={
        "bounds": GroupUI(
            title="Bounds",
            collapsed=False,
            extra_rows=[
                RowSpec(
                    "reset_bounds",
                    ButtonUI(label="Reset bounds"),
                    on_click=_on_reset_bounds,
                    position="above",
                ),
            ],
        ),
    },
    extra_rows=[
        RowSpec(
            "enable_bounds",
            CheckboxUI(title="Bounds enabled"),
            value=True,
            on_change=_on_toggle_bounds,
            position="above",
        ),
        RowSpec("detect", ButtonUI(label="Detect rim"), on_click=_on_detect, position="above"),
        RowSpec("status", MarkdownUI(), "**Idle**"),
    ],
)


# ── 4. Runtime API (set_visible / set_enabled / set_title / set_options / …) ──
runtime_view = ParamsView(
    {"alpha": 1.0, "beta": 2.0, "mode": "solid"},
    styles={
        "alpha": SliderUI(title="Alpha", min=0.0, max=5.0),
        "beta": SliderUI(title="Beta", min=0.0, max=5.0),
        "mode": DropdownUI(title="Mode", options=["solid", "wire"]),
    },
    min_width=Size.px(240),
    on_change=_on_change,
)

_beta_visible = True
_alpha_enabled = True


async def _toggle_beta(value: Any, event: ControlEvent) -> None:
    global _beta_visible
    _beta_visible = not _beta_visible
    runtime_view.set_visible("beta", _beta_visible)


async def _toggle_alpha(value: Any, event: ControlEvent) -> None:
    global _alpha_enabled
    _alpha_enabled = not _alpha_enabled
    runtime_view.set_enabled("alpha", _alpha_enabled)


async def _rename_alpha(value: Any, event: ControlEvent) -> None:
    runtime_view.set_title("alpha", "Alpha (renamed)")


async def _change_options(value: Any, event: ControlEvent) -> None:
    runtime_view.set_options("mode", ["solid", "wire", "xray"])


async def _add_gamma(value: Any, event: ControlEvent) -> None:
    try:
        runtime_view.add("gamma", 0.5, SliderUI(title="Gamma", min=0.0, max=5.0))
    except ValueError:
        print("  gamma already exists")


async def _remove_gamma(value: Any, event: ControlEvent) -> None:
    runtime_view.remove("gamma")


async def _reset_state(value: Any, event: ControlEvent) -> None:
    runtime_view.set_state({"alpha": 1.0, "beta": 2.0, "mode": "solid"})


runtime_buttons = [
    ButtonView("toggle_beta", label="Toggle beta", on_click=_toggle_beta),
    ButtonView("toggle_alpha", label="Toggle alpha", on_click=_toggle_alpha),
    ButtonView("rename_alpha", label="Rename alpha", on_click=_rename_alpha),
    ButtonView("change_options", label="Change options", on_click=_change_options),
    ButtonView("add_gamma", label="Add gamma", on_click=_add_gamma),
    ButtonView("remove_gamma", label="Remove gamma", on_click=_remove_gamma),
    ButtonView("reset_state", label="Reset state", on_click=_reset_state),
]


# ── 5. Ergonomics (title_from_name + dense) ─────────────────────────────────
@dataclass
class DenseParams:
    sphere_radius: float = 2.0
    max_segments: int = 64
    wireframe_mode: bool = False


dense_view = ParamsView(
    DenseParams(),
    min_width=Size.px(240),
    on_change=_on_change,
    title_from_name=True,
    dense=True,
)


layout = SplitView(
    orientation="horizontal",
    sizes=[Size.percent(40), Size.percent(60)],
    children=[
        StackView(
            "vertical",
            [
                GroupView("Spec fields", [spec_view]),
                GroupView("Inference", [inferred_view]),
                GroupView("Nested + extra rows", [nested_view]),
                GroupView("Runtime API", runtime_buttons + [runtime_view]),
                GroupView("title_from_name + dense", [dense_view]),
            ],
        ),
        SceneView(""),
    ],
)

viz.show(layout=layout)
print("Each panel demonstrates a ParamsView feature. Press Ctrl+C to exit.")
viz.wait()
````
