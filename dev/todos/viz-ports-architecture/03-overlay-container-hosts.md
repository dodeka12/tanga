# Phase 3 — Fold banners/dialogs/editor into `OverlayContainer`

## Goal

Move the `BannerHost`/`DialogHost`/`EditorHost` state and methods into
`OverlayContainer` (banners, draggable dialogs, editor) and delete the three
hosts.  Behavior-preserving wire messages (`banner_*`, `dialog_*`, `editor_*`).

## Files

- Edit: `py/pytanga/viz/_layout.py` (`OverlayContainer`)
- Edit: `py/pytanga/viz/_hosts.py` (delete 3 hosts)
- Edit: `py/pytanga/viz/visualizer.py` (wire + routes)

## Steps

- [x] **3.1 — Move state + methods**
  - `_banners`/`_banner_counter`, `_dialogs`/`_dialog_counter`, editor `on_close`
    into `OverlayContainer`; move `show_banner`/`alert`/`confirm`/`remove_banner`/
    `clear_banners`, `show_dialog`/`remove_dialog`/`clear_dialogs`, `open_editor`
    and their `_on_close`/`_on_accept` handlers.
- [x] **3.2 — Delete hosts**
  - Remove `BannerHost`/`DialogHost`/`EditorHost`; `OverlayContainer` uses
    `transport` for send/register.
- [x] **3.3 — Route + wire**
  - `banner_closed`/`editor_closed`/`close`/`accept` routes point at the overlay
    container; `Visualizer.show_banner`/`show_dialog`/`open_editor` forwarders.
- [x] **3.4 — Tests**
  - Repoint monkeypatches (`viz._banner_host._push_*` → `viz.layout.overlay._push_*`).

## Validation

`uv run pytest py/tests/viz -q`
