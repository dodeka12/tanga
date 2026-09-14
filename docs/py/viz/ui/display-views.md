# Display Views

Three read-only content views render text, markdown, and a live log inside a
layout (no scene required):

| Class | Purpose |
|-------|---------|
| `LabelView` | A single line of text with a configurable `font_size` (default `14` px). |
| `MarkdownView` | A multi-line block of rendered markdown with KaTeX math (`$…$` / `$$…$$`). |
| `LogView` | A live, auto-scrolling two-column (time \| message) log. |

`LabelView` and `MarkdownView` are **display-only controls**: they carry a
`value` and can be updated in place after creation via `view.set_value(value)`,
which pushes the same `control_update` message used by every other control:

```python
label = LabelView("label", value="hello", font_size=20)
markdown = MarkdownView("md", value="# Title\n\n$E = mc^2$")
```

`LogView` is not a control — its lines are appended from the backend, so it has
its own `log_update` push.  `log()` captures a UTC timestamp and accepts either
a string (stored as `message`) or a dict (whose keys are folded into the line);
the frontend shows `message`, falling back to JSON of the other keys.  The
first column shows the timestamp in the browser's local timezone — by default
just the time with microseconds; `show_date=True` adds the date and
`show_utc_offset=True` adds the local offset to UTC:

```python
log = LogView(id="log", max_history=1000, show_date=True, show_utc_offset=True)   # None = unlimited
log.log("plain line")
log.log({"message": "structured", "level": "info"})
log.get_log()          # -> list[dict] (copies)
log.write_file(path)   # JSON lines (one dict per line)
log.load_file(path)    # replace (truncated to max_history)
log.clear()
```

Rows alternate shading, new lines auto-scroll into view (unless the user has
scrolled up), and `max_history` drops the oldest lines on both the backend and
the browser.

## Examples

- `py/examples/viz/ui/static/display_views.py` — `LabelView` and `MarkdownView`
  in a split layout.
- `py/examples/viz/ui/static/log_view.py` — a live `LogView`.

## See Also

- [Split Views](split-views.md) — placing display views in a layout
