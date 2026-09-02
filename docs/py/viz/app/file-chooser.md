# File Chooser

A file chooser control lets the user enter a file **path** (text field) or pick
one from a **custom file browser** (a modal dialog).  The browser is driven by
the backend, which reads the Linux filesystem and sends the listing over the
WebSocket — so it returns real absolute paths (unlike the browser's native file
dialog).

## Using it

```python
async def init(self):
    self.viz.add_file_chooser(
        "data_file",
        label="Data file",
        placeholder="/path/to/file",
        root="/home/me",          # browse root (defaults to ~)
        on_change=self.on_file,
    )

async def on_file(self, path, event):
    print("selected:", path)
```

- `value` — initial path.
- `root` — browse root (defaults to the home directory).  The text field
  accepts any absolute path regardless of `root`.
- `on_change(path, event)` — fires when the user types a path or selects a
  file in the browser.

The control is also available as a `FileChooserView` for layouts/panels, like
`ButtonView` — but that view renders only the **file-selection listing** (no
path field, no "Browse…" button, no path display).  Compose a path field and
browse button yourself, or use `FileChooserDialog` to show the listing in a
full dialog with a path line and OK/Cancel:

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

- `py/examples/viz/interaction/file_chooser.py`
