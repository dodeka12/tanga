# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""toolbar.py — Four toolbars, one per alignment, stacked in a vertical split.

Builds a vertical :class:`~pytanga.viz.SplitView` with four equal panes.  Each
pane is a :class:`~pytanga.viz.ToolbarView` holding the same mixed control set —
a labelled button, a :class:`~pytanga.viz.SliderView`, a
:class:`~pytanga.viz.DropdownView`, three icon-only buttons, and an
auto-oriented :class:`~pytanga.viz.SeparatorView` — but with a different
``justify``, showing the four toolbar alignments at once:

- ``EStackJustify.START`` — controls packed left;
- ``EStackJustify.END`` — controls packed right;
- ``EStackJustify.CENTER`` — controls block-centered;
- ``EStackJustify.SPACE_EVENLY`` — controls equally spaced across the row.

Each toolbar leads with a button labelled with its alignment so the rows are
self-describing; the three icon-only buttons show how ``icon_only`` buttons
render as small square icon tiles, separated from the other controls by an
auto-oriented ``SeparatorView``.  The top two rows pass ``border=False`` to
show the borderless toolbar, while the bottom two keep the default thin
outline; the last row also sets an explicit ``gap``.

Run with:  uv run python py/examples/viz/ui/controls/toolbar.py

Keywords: toolbar, alignment, split view, slider, dropdown, icon, separator, layout
"""

from pytanga.viz import (
    ButtonView,
    DropdownView,
    EIconMaterial,
    EStackJustify,
    SeparatorView,
    Size,
    SliderView,
    SplitView,
    ToolbarView,
    Visualizer,
)

viz = Visualizer(reuse_existing=False, title="Tanga — Toolbar Alignments")


def _row(tag, label, justify, **kwargs):
    """A toolbar holding a label button, a slider, a dropdown, a separator, and icons."""
    return ToolbarView(
        [
            ButtonView(f"lbl_{tag}", label=label),
            SliderView(f"slider_{tag}", label="Value", min=0.0, max=1.0, value=0.5),
            DropdownView(
                f"dropdown_{tag}",
                label="Mode",
                options=["A", "B", "C"],
                value="A",
            ),
            SeparatorView(),
            ButtonView(f"icon_{tag}_add", icon=EIconMaterial.ADD, icon_only=True),
            ButtonView(f"icon_{tag}_edit", icon=EIconMaterial.EDIT, icon_only=True),
            ButtonView(f"icon_{tag}_delete", icon=EIconMaterial.DELETE, icon_only=True),
        ],
        justify=justify,
        **kwargs,
    )


# Four toolbars, one per alignment.  The top two are borderless (`border=False`);
# the bottom two keep the default thin outline.  The last row also sets an
# explicit `gap`.
layout = SplitView(
    orientation="vertical",
    sizes=[Size.percent(25), Size.percent(25), Size.percent(25), Size.percent(25)],
    children=[
        _row("start", "Start", EStackJustify.START, border=False),
        _row("end", "End", EStackJustify.END, border=False),
        _row("center", "Center", EStackJustify.CENTER),
        _row("evenly", "Equally spaced", EStackJustify.SPACE_EVENLY, gap=8),
    ],
)

viz.show(layout=layout)
print("Four toolbar alignments are shown at a single URL. Press Ctrl+C to exit.")
viz.wait()
