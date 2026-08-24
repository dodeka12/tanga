# Jupyter Notebooks

The `Visualizer` detects Jupyter/IPython automatically and adapts behaviour
for notebook environments: `show()` renders inline, `run()` is unavailable,
and the serverless `display_snapshot()` produces static embeds.

## Auto-detection

- `open_browser` defaults to `False` (no popup).
- `run()` is **not** available — it would block the kernel indefinitely.
- Use the `start_server()` / `flush()` / `stop_server()` non-blocking pattern
  instead (or `show()` to also open a browser).
- When the `Visualizer` object is the last expression in a notebook cell,
  it renders an inline `<iframe>` via the `_repr_html_()` method.

## Live vs static

| Need | Use | Page |
|------|-----|------|
| Rotate / zoom / animate live | `start_server()` + `flush()` + `_repr_html_()` | [Live inline display](live.md) |
| Quick static snapshot | `display_snapshot()` | [Static inline display](static.ipynb) |

## How it works

- `start_server()` launches the aiohttp server in a background daemon thread.
  The server survives across notebook cells until `stop_server()` is called.
- `flush()` pushes scene state to all connected browsers — call it after
  adding or modifying entities.
- `_repr_html_()` returns an `<iframe>` pointing to the server URL. Jupyter
  calls this automatically when the `Visualizer` object is the last expression
  in a cell.
- `stop_server()` releases the port and terminates the background thread.
  Always call it when done to free resources.

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Live inline display](live.md) | `start_server()`/`flush()`/`_repr_html_()`, idempotent `show()`/`display()`, `display_row(mode="live")` |
| [Static inline display](static.ipynb) | `display_snapshot()` and `display_row(mode="static")` — serverless, embeddable viewers |

## Limitations

- **Remote Jupyter** (Colab, Binder, remote kernels): The iframe points to
  `localhost`, which is the **server machine**, not your local browser. The
  viewer won't be reachable. Open the printed URL in a separate browser tab
  on the machine running the kernel.
- **Port conflicts:** `start_server()` defaults to port 8765; pass `port=...`
  to choose another, or `port=0` to auto-pick a free port.
- **Multiple scenes:** Create named scenes via ``viz.scene("name")`` instead
  of multiple ``Visualizer`` instances — all scenes share one server on one
  port.

