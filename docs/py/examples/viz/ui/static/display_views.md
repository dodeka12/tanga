# Settable label and markdown panes in a vertical split

**Keywords:** split view · label · markdown · KaTeX · control update · layout

Builds a vertical `~pytanga.viz.SplitView` with a
`~pytanga.viz.LabelView` pane (configurable `font_size`) and a
`~pytanga.viz.MarkdownView` pane (rendered markdown with KaTeX math).
Both are read-only content views that still carry a `value`, so the leading
`~pytanga.viz.ButtonView` updates them live via `viz.set_control`
(the same `control_update` path every other control uses).

## Run

```bash
uv run python py/examples/viz/ui/static/display_views.py
```

## Source

[`viz/ui/static/display_views.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/ui/static/display_views.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""display_views.py — Settable label and markdown panes in a vertical split.

Builds a vertical :class:`~pytanga.viz.SplitView` with a
:class:`~pytanga.viz.LabelView` pane (configurable ``font_size``) and a
:class:`~pytanga.viz.MarkdownView` pane (rendered markdown with KaTeX math).
Both are read-only content views that still carry a ``value``, so the leading
:class:`~pytanga.viz.ButtonView` updates them live via ``viz.set_control``
(the same ``control_update`` path every other control uses).

Run with:  uv run python py/examples/viz/ui/static/display_views.py

Keywords: split view, label, markdown, KaTeX, control update, layout
"""

from pytanga.viz import ButtonView, LabelView, MarkdownView, Size, SplitView, Visualizer

viz = Visualizer(reuse_existing=False, title="Tanga — Label & Markdown Views")

markdown_value = r"""# Rendered Markdown

- a bullet list
- **bold** and *italic*
- `inline code`

Inline math: $E = mc^2$.

Display math:

$$
\int_{-\infty}^{\infty} e^{-x^2}\,dx = \sqrt{\pi}
$$
"""


async def on_update(_value, _event):
    """Update both display views in place (pushed via ``control_update``)."""
    viz.set_control("label", "Updated at runtime ✓")
    viz.set_control("markdown", r"**Live update** — now $\nabla^2 \phi = 0$.")


layout = SplitView(
    orientation="vertical",
    sizes=[Size.percent(10), Size.percent(20), Size.percent(70)],
    children=[
        ButtonView("btn_update", label="Update both views", on_click=on_update),
        LabelView("label", value="Hello, world!", font_size=24),
        MarkdownView("markdown", value=markdown_value),
    ],
)

viz.show(layout=layout)
print("Click the button to update the label and markdown live. Press Ctrl+C to exit.")
viz.wait()
````
