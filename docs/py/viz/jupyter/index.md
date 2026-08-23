# Jupyter Notebooks

The visualizer auto-detects Jupyter/IPython and switches to inline rendering:
`show()` renders inline, `run()` is unavailable, and the serverless
`display_snapshot()` produces static embeds.

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Live inline display](live.md) | `start_server()`/`flush()`/`_repr_html_()`, idempotent `show()`/`display()`, `display_row(mode="live")` |
| [Static inline display](static.ipynb) | `display_snapshot()` and `display_row(mode="static")` — serverless, embeddable viewers |
