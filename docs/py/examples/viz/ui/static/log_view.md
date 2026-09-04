# A live, auto-scrolling two-column log in a split pane

**Keywords:** split view · log · streaming · history · layout

Builds a vertical `~pytanga.viz.SplitView` with a
`~pytanga.viz.ButtonView` pane and a `~pytanga.viz.LogView` pane.
The button appends lines (a plain string and a structured dict) via
`log_view.log`, which pushes `log_update` to the browser; the log
auto-scrolls to the newest line, alternates row shading, and keeps only the
last `max_history` entries.

## Run

```bash
uv run python py/examples/viz/ui/static/log_view.py
```

## Source

[`viz/ui/static/log_view.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/ui/static/log_view.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""log_view.py — A live, auto-scrolling two-column log in a split pane.

Builds a vertical :class:`~pytanga.viz.SplitView` with a
:class:`~pytanga.viz.ButtonView` pane and a :class:`~pytanga.viz.LogView` pane.
The button appends lines (a plain string and a structured dict) via
``log_view.log``, which pushes ``log_update`` to the browser; the log
auto-scrolls to the newest line, alternates row shading, and keeps only the
last ``max_history`` entries.

Run with:  uv run python py/examples/viz/ui/static/log_view.py

Keywords: split view, log, streaming, history, layout
"""

from itertools import count

from pytanga.viz import ButtonView, LogView, Size, SplitView, Visualizer

viz = Visualizer(reuse_existing=False, title="Tanga — Live Log")

log = LogView(id="log", max_history=100)
log.log("Log view ready.")
log.log({"message": "structured line", "level": "info"})

# The full data API: `log.get_log()` -> list[dict], `log.write_file(path)`,
# `log.load_file(path)`, and `log.clear()`.
_counter = count()


async def on_append(_value, _event):
    n = next(_counter)
    log.log(f"Appended line #{n}")
    log.log({"message": "structured event", "step": n, "level": "warn"})


layout = SplitView(
    orientation="vertical",
    sizes=[Size.percent(15), Size.percent(85)],
    children=[
        ButtonView("btn_append", label="Append lines", on_click=on_append),
        log,
    ],
)

viz.show(layout=layout)
print("Click the button to append live log lines. Press Ctrl+C to exit.")
viz.wait()
````
