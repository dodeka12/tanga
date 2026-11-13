# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""serve-visibility-smoke.py — headless server for the view-visibility smoke.

Builds a layout whose visibility state is exercised from both sides:

* a ``GroupView`` created with ``visible=False`` (serialized state must hide the
  whole pane at build time),
* a ``ParamsView`` whose ``alpha`` row is hidden via ``SliderUI(visible=False)``
  (the row title must disappear with the control),
* a probe group that stays visible, so layout space can be compared,
* toolbar buttons that toggle group/row visibility at runtime and re-push the
  layout.

Prints the URL for ``js/dev/tests/visibility-smoke.mjs``.

Run with:  uv run python js/dev/tests/serve-visibility-smoke.py
"""

from typing import Any

from pytanga.viz import (
    ButtonView,
    ControlEvent,
    GroupView,
    ParamsView,
    SliderUI,
    SliderView,
    SplitView,
    ToolbarView,
    Visualizer,
)


def main() -> None:
    viz = Visualizer(
        title="Tanga — view visibility smoke",
        add_default_axes=False,
        add_default_grid=False,
    )

    hidden_group = GroupView(
        "Hidden group",
        [SliderView("hidden_group_slider", value=1.0)],
        visible=False,
    )
    probe_group = GroupView("Probe group", [ButtonView("probe_btn", label="Probe")])
    params = ParamsView(
        {"alpha": 1.0, "beta": 2.0},
        styles={
            "alpha": SliderUI(title="Alpha", visible=False),
            "beta": SliderUI(title="Beta"),
        },
    )

    async def _show_group(_value: Any, _event: ControlEvent) -> None:
        hidden_group.set_visible(True)

    async def _hide_group(_value: Any, _event: ControlEvent) -> None:
        hidden_group.set_visible(False)

    async def _show_row(_value: Any, _event: ControlEvent) -> None:
        params.set_visible("alpha", True)

    async def _hide_row(_value: Any, _event: ControlEvent) -> None:
        params.set_visible("beta", False)

    async def _repush(_value: Any, _event: ControlEvent) -> None:
        viz.set_layout(layout, name="demo")

    toolbar = ToolbarView(
        [
            ButtonView("btn_show_group", label="Show group", on_click=_show_group),
            ButtonView("btn_hide_group", label="Hide group", on_click=_hide_group),
            ButtonView("btn_show_row", label="Show row", on_click=_show_row),
            ButtonView("btn_hide_row", label="Hide row", on_click=_hide_row),
            ButtonView("btn_repush", label="Re-push", on_click=_repush),
        ]
    )
    layout = SplitView("vertical", [toolbar, hidden_group, probe_group, params])
    viz.set_layout(layout, name="demo")

    viz.start_server(host="localhost", port=0)
    print(f"SMOKE_URL={viz.url}", flush=True)
    viz.wait()


if __name__ == "__main__":
    main()
