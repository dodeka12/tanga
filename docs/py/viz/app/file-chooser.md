# File Chooser

A file chooser control lets the user enter a file **path** (text field) or pick
one from a **custom file browser** (a modal dialog).  The browser is driven by
the backend, which reads the Linux filesystem and sends the listing over the
WebSocket — so it returns real absolute paths (unlike the browser's native file
dialog).

## Using it

The file browser is driven by the backend. Two surfaces expose it:

- `FileChooserView` — a declarative control view that renders the directory
  listing (no path field or "Browse…" button — compose those yourself, or use
  the dialog below). Mount it in a layout with `viz.add(view)` / `set_layout`.
- `FileChooserDialog` — a full modal dialog with a path line and OK/Cancel,
  shown with `viz.show_dialog(...)`.

```python
async def init(self):
    self.viz.add(
        FileChooserView(
            "data_file",
            label="Data file",
            value="/path/to/file",      # initial path
            root="/home/me",            # browse root (defaults to ~)
            on_change=self.on_file,
        )
    )

async def on_file(self, path, event):
    print("selected:", path)
```

- `value` — initial path.
- `root` — browse root (defaults to the home directory). The listing clamps to
  `root` when set.
- `on_change(path, event)` — fires when the user selects a file in the browser.

For the full path-field + browse-button experience, use `FileChooserDialog`
instead:

```python
viz.show_dialog(
    FileChooserDialog("data_file", root="/home/me", on_accept=on_file),
    title="Select a data file",
)
```

Selecting a file fills the dialog's path line; `OK` fires `on_accept(path)` and
closes, while `Cancel`/✕ fire `on_close`.  The dialog has a fixed default size
(and a drag-to-resize corner).

## Opening the browser from the backend

```python
self.viz.open_file_chooser("data_file")                # opens at value/root
self.viz.open_file_chooser("data_file", path="/tmp")   # opens at a path
```

## Modal behavior

While open, the browser is modal: the surrounding visualization is grayed out
and blocked (like a non-dismissable banner), until the user selects a file or
cancels.

## Example

- `py/examples/viz/ui/controls/file_chooser.py`
