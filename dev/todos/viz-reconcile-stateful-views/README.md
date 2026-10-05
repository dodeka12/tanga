# Viz reconcile stateful views — Overview

**Created:** 2026-10-05 | **Status:** Done | **Branch:** `fix/small-bugs`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Extend frontend layout reconciliation so **every content view** survives a
`view_layout` re-push, not just scene panes and the basic form controls.  Today
the `REUSABLE_TYPES` allow-list (`templates/views/reconcile.js`) excludes
`log_view`, `file_chooser_view`, `table_view`, and `progress_bar_view`, so those
are torn down and rebuilt on every `set_layout(...)`.  For `log_view` this is the
reported bug (`_input/pytanga-log-view-destroyed-view-forgets-registry-entry.md`):
a stable-id `LogView` stops receiving `.log()` updates after any re-push because
the orphaned old view's `destroy()` forgets the `_messageViews` entry the fresh
view just installed.  We also preserve `group` (a titled container with collapse
state) per explicit request; the remaining pure-layout containers (`split`,
`stack`, `toolbar`, `menu`) stay rebuilt.  As part of preserving `group`, its
`collapsed` state becomes backend-synced (`on_toggle` + `set_collapsed`, pushed
via `control_state`), so the backend can read and programmatically set it.

## Architecture (short)

- **Identity = `View.id` + node `type`.** `reconcile.js` decides, per serialized
  node, whether to reuse the live view (same id **and** allow-listed type),
  create a new one, or orphan the old one.  `buildViewTree` (`build.js`) reuses
  a live view by calling `update(node)` and re-parenting it; `_viewRegistry`
  collects the next build's live views and `_buildLayout` (`viewer.js`) destroys
  the orphaned set afterward.
- **Re-mount re-renders.** A reused control is re-mounted by its new container
  (`addChild` → `mount` → `_onMounted` → `ControlView.rerender()`), so `update()`
  only refreshes JS fields and the DOM is rebuilt from them.  `MessageView` is a
  plain `View` with a custom `_onMounted`, so it must be made idempotent to keep
  its accumulated rows.
- **Registry teardown must be identity-safe.** Registry-backed views
  (`MessageView` → `_messageViews`, `FileChooserView` → `fileBrowser._views`)
  must only forget their entry when it still points at `this`, so a stale
  orphan-destroy can never clobber a same-id successor.

### Fixed contract (do not change across phases)

1. **Final `REUSABLE_TYPES`** = the existing set **plus**
   `log_view`, `file_chooser_view`, `table_view`, `progress_bar_view`, `group`.
   Not reusable (still rebuilt): `split`, `stack`, `toolbar`, `menu`.
2. **`buildViewTree` reuse branch pattern** for every newly-reusable type:
   `if (existing) { existing.update(node); view = existing; } else { view = new X(...); }`,
   then `applySizeSpecs(view, node)` and (for containers) re-add children.
3. **`update(node)` refreshes fields** with `??` fallback to the current value;
   it never re-runs the constructor or `GroupView._setupChrome`.
4. **`MessageView.destroy()` / `FileChooserView.destroy()` are identity-safe**
   (only forget the registry entry when it still points at `this`).
5. **`control_state` gains a `collapsed` field** for `GroupView` (resolved via
   `_viewRegistry`, not `_controlRegistry`); the user toggle reports through the
   existing `control:group_toggle` route, which mutates `GroupView.collapsed` and
   fires `on_toggle`.

## Decisions (confirmed)

- Preserve `log_view`, `file_chooser_view`, `table_view`, `progress_bar_view`,
  and `group`; keep rebuilding `split`/`stack`/`toolbar`/`menu`.
- `MessageView` preserves its live DOM history across a re-push (the
  re-serialized `node.lines` is ignored on reuse); `_onMounted` is guarded to
  append `initialLines` only once.
- `group` reuse clears its existing children (via `removeChild`) before
  `update()` + re-add, mirroring `scene_view`'s clear-overlays-then-rebuild.
- Identity-safe teardown is defense-in-depth; the primary fix is making the
  views reusable so the orphan-destroy race never fires on an id-stable re-push.
- Collapse sync reuses `control_state` (a `collapsed` field), not a new message
  type; `collapsed` is backend-authoritative, so group `update()` applies
  `node.collapsed`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-content-view-reuse.md](./01-content-view-reuse.md) | Make the 4 content leaf views reusable + identity-safe teardown (fixes the log-view bug) |
| 2 | [02-group-collapse-roundtrip.md](./02-group-collapse-roundtrip.md) | Backend-sync `GroupView.collapsed` (`on_toggle` + `set_collapsed` via `control_state`) |
| 3 | [03-group-view-reuse.md](./03-group-view-reuse.md) | Make `group` reusable (preserve title/collapse state) |
| 4 | [04-regression-tests.md](./04-regression-tests.md) | Headless log-view re-push regression smoke + Python-side guard + group collapse smoke |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Update architecture docs + branch changelog |

## Testing as you go

```bash
node js/dev/tests/check-syntax.mjs                # JS parse gate (all templates + tests)
node --test 'js/dev/tests/*.test.mjs'             # JS unit tests (reconcile planner)
uv run pytest py/tests/viz -q                     # Python viz suite
uv run python tools/build-viewer-js.py --check    # export bundle drift gate
uv run mkdocs build --strict                      # docs
```

> The live frontend (`templates/viewer.js` + `templates/views/` +
> `templates/controls/`) is served directly as ES modules;
> `build-viewer-js.py --check` gates only the export bundle (`js/tanga-viewer.js`).

## Non-goals

- No server-side diffing: `set_layout` still re-serializes and pushes the whole
  `view_layout`; the *frontend* reconciles it.
- `split`/`stack`/`toolbar`/`menu` remain recreated (pure flexbox containers).
- No change to Python view/id generation or the `view_layout` wire format.
- No new wire message type: the collapse round-trip reuses the existing
  `control_state` channel (a new `collapsed` field) and the existing
  `control:group_toggle` route.
- No change to the `control_update`/`scene_update`/`log_update` incremental
  channels (beyond keeping the registries that receive them intact).
