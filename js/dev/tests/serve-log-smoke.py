# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""serve-log-smoke.py — headless server for the LogView reconcile Playwright smoke.

Builds a layout with a stable-id ``LogView(id="solver_log")`` plus a collapsed
``GroupView``, and a toolbar button that re-pushes the same layout (same stable
log id) and then logs a line.  The smoke asserts the line still renders and the
group stays collapsed after the re-push.

Run with:  uv run python js/dev/tests/serve-log-smoke.py
"""

from typing import Any

from pytanga.viz import (
    ButtonView,
    ControlEvent,
    GroupView,
    LogView,
    SplitView,
    ToolbarView,
    Visualizer,
)


def main() -> None:
    viz = Visualizer(
        title="Tanga — log-view reconcile smoke",
        add_default_axes=False,
        add_default_grid=False,
    )

    log_view = LogView(id="solver_log", max_history=200)
    group = GroupView("Controls", collapsed=True)

    async def _on_repush(_value: Any, _event: ControlEvent) -> None:
        # Re-push the same layout (same stable LogView id), then log a line the
        # smoke asserts is rendered.
        viz.set_layout(layout, name="demo")
        log_view.log("after re-push")

    toolbar = ToolbarView(
        [ButtonView("btn_repush", label="Re-push + log", on_click=_on_repush)]
    )
    layout = SplitView("vertical", [toolbar, log_view, group])
    viz.set_layout(layout, name="demo")

    viz.start_server(host="localhost", port=0)
    print(f"SMOKE_URL={viz.url}", flush=True)
    viz.wait()


if __name__ == "__main__":
    main()
