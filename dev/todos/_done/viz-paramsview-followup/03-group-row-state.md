# Phase 3 — Group row state: visible / enabled / title (item 4, group rows)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (`control_state`
> dispatch and the `{visible}`/`{collapsed}` view routing in `viewer.js`) and
> `docs/dev/architecture/viz-architecture.md` (`GroupView` serialization).  This
> extends the existing `control_state` view-routing pattern to `{enabled}`/`{title}`
> and adds state fields to `GroupView` (mirroring `collapsed`).

## Goal

`set_visible`/`set_enabled`/`set_title` work on a group row: hiding a group,
greying + collapsing + locking a group, and renaming its header.

## Files

- **Edit** `py/pytanga/viz/views/group_view.py` — `visible`/`enabled` fields +
  `set_visible`/`set_enabled`/`set_title`; serialize non-defaults.
- **Edit** `py/pytanga/viz/templates/views/group-view.js` — `setEnabled`/`setTitle`,
  `enabled` in constructor/`update`.
- **Edit** `py/pytanga/viz/templates/viewer.js` — route `{enabled}`/`{title}` to the group.
- **Edit** `py/pytanga/viz/templates/views/build.js` — pass `enabled` to new groups.
- **Edit** `py/pytanga/viz/templates/themes/views/group-view.css` — grey header rule.
- **Edit** `py/tests/viz/test_views.py`.

## Steps

- [x] **3.1 — Python `GroupView` model**
  - Add `visible: bool = True` and `enabled: bool = True` to `GroupView.__init__`
    (keyword, stored on `self`).
  - Add `set_visible(visible)` / `set_enabled(enabled)` / `set_title(title)` that
    mutate state and push via `self._push_state` (`{visible}` / `{enabled}` /
    `{title}`) when set (mirror `set_collapsed`).
  - `_serialize` emits `"visible": False` / `"enabled": False` only when non-default.
- [x] **3.2 — frontend `GroupView`**
  - Add `setEnabled(enabled)`: toggle `.tanga-group-disabled` on `this.el`,
    collapse when disabled (`this.setCollapsed(true)`), and disable `_toggleBtn`
    (re-enabling re-arms the toggle without force-expanding).
  - Add `setTitle(title)`: update `this.title` and re-`_renderTitle()`.
  - Accept `enabled` in the constructor and apply the disabled state after
    `_setupChrome()`; handle `enabled` in `update(node)`.
- [x] **3.3 — `viewer.js` routing**
  - In the `control_state` branch, route `{enabled}` → `host.setEnabled(...)` and
    `{title}` **without** `row` → `host.setTitle(...)` (keep the existing
    `{row, title}` params-row branch).
- [x] **3.4 — `build.js` + CSS**
  - Pass `enabled: node.enabled` when constructing a new `GroupView`.
  - Add `.tanga-group.tanga-group-disabled .tanga-group-header { opacity:
    var(--tanga-disabled-opacity); }` (and grey the title/toggle).
- [x] **3.5 — tests**
  - `set_visible`/`set_enabled`/`set_title` mutate + push `control_state`;
    serialization includes `visible`/`enabled` only when non-default.

## Validation

```bash
uv run pytest py/tests/viz/test_views.py -q && node js/dev/tests/check-syntax.mjs
```

## Notes

- `visible` needs no new frontend logic — the existing `control_state {visible}`
  → `host.setHidden(!visible)` path already covers any registered view.
- `enabled` is the only group state with a "collapse + lock" side effect; do not
  force-expand on re-enable.
