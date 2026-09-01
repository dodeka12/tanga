# Phase 2 — `GroupView` icon/icon_only + borderless fold button

## Goal

Add an optional leading icon (or icon-only) to the layout `GroupView` title bar
and make the fold/unfold button borderless (icon, not text).

## Files

- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/templates/views/group-view.js`
- Edit: `py/pytanga/viz/templates/views/build.js`
- Edit: `py/pytanga/viz/templates/controls-panel.js` (CSS only, for panel parity)

## Steps

- [x] **2.1 — Python `GroupView` fields (`views.py`)**
  - Add `icon: Icon | None = None` and `icon_only: bool = False` to
    `GroupView.__init__` (keyword-only), store on `self`.
  - In `GroupView._serialize`, emit `result["icon"] = str(self.icon)` only when
    `icon is not None`, and `result["icon_only"] = self.icon_only`.

- [x] **2.2 — Frontend `GroupView` (`group-view.js`)**
  - Accept `icon = null` / `icon_only = false` in the constructor options.
  - Import `createIconElement` from `../controls-panel.js`.
  - In `_setupChrome`, when `icon` is set, render it before the title (and skip
    the title `span` when `icon_only`).
  - Replace the fold `button` text `▾/▴` with a borderless icon
    (`createIconElement` of `material:expand_more` / `material:expand_less`);
    set `background: 'none'` and `border: 'none'`.

- [x] **2.3 — Build threading (`build.js`)**
  - In the `group` branch, pass `icon: node.icon, icon_only: node.icon_only` to
    `new GroupView({...})`.

- [x] **2.4 — Panel parity (CSS, optional)**
  - In `controls-panel.js` injected CSS, change `.tanga-group-toggle` to
    `border: none` (keep sizing/centering) so the legacy panel group toggle is
    also borderless until it is retired in Phase 10.

- [x] **2.5 — Tests / smoke**
  - `test_views.py`: `GroupView` serializes `icon` (and omits it when `None`)
    and `icon_only`.
  - Extend `dev/src/js-tests/group-view-smoke.html` (or a new sibling) to assert
    an icon is rendered and the toggle button has `border-style: none`.

## Validation

`uv run pytest py/tests/viz/test_views.py -q && node --check py/pytanga/viz/templates/views/group-view.js && node --check py/pytanga/viz/templates/views/build.js`
