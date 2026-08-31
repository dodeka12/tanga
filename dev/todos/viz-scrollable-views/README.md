# Scrollable stack & group panes — Overview

**Created:** 2026-08-31 | **Status:** In progress | **Branch:** `fix/file-chooser-bug`

## Goal

Let a `StackView`/`GroupView` pane inside a `SplitView` optionally scroll
instead of being clipped when its content outgrows the pane. A new `scrollable`
flag — off by default — decouples the container's content-derived size along its
stack axis so the split is *allowed* to shrink it, and turns the pane into an
`overflow: auto` scroll region with a custom thin, dark scrollbar that appears
only when the content actually overflows.

## Architecture (short)

Today a `StackView` sizes to its content (`stack-size.js` →
`stackMinSize`/`stackPreferredSize`), and `SplitView` propagates that minimum
upward (`split-resolver.js` `deriveMinSize`). A group pane can therefore never
be smaller than its full content, so `SplitView` clips it (`overflow: hidden`)
with no scrollbar. The fix is two coordinated parts:

1. **Size decoupling** — when `scrollable`, `StackView.minSizePx`/`preferredPx`
   stop deriving from content along the stack's **main axis** and report only
   the explicit min/preferred (else `0`/`null`).
2. **Scroll region** — when `scrollable`, the scroll container gets
   `overflow: auto` plus a `.tanga-scroll` class; `GroupView` pins its title bar
   and scrolls only the content region below it.

### Fixed contract (decided up front)

- **Wire:** `"scrollable": <bool>` is serialized on both `stack` and `group`
  nodes (always present, like `collapsed`).
- **Python:**
  `StackView(direction, children=None, *, scrollable=False, **kwargs)`;
  `GroupView(title, children=None, *, direction="vertical", position=None,
  collapsed=False, scrollable=False, **kwargs)`.
- **JS:** `new StackView({ direction, scrollable = false, children })`;
  `new GroupView({ title, direction, position, collapsed, scrollable = false })`.
- **Scroll axis:** decouple min/preferred only along `stackMainAxis(direction)`;
  the cross-axis min stays content-derived. The scroll region uses
  `overflow: auto` (both axes) so a cross-axis overflow scrolls too.
- **Custom scrollbar:** injected once as `<style id="tanga-scroll-styles">` with
  `.tanga-scroll` rules — WebKit `::-webkit-scrollbar` (thin ~8px dark thumb) and
  Firefox `scrollbar-width: thin; scrollbar-color: …` — matching the `#1a1a2e`
  theme.

## Decisions (confirmed)

- Flag name `scrollable`.
- Add to both `StackView` and `GroupView` (`GroupView` inherits the behaviour).
- Custom scrollbar styling, not the native OS scrollbar.
- No new `ScrollView` node type.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-scrollable-model.md](./01-python-scrollable-model.md) | `scrollable` flag + serialization on `StackView`/`GroupView` (+ Python tests). |
| 2 | [02-frontend-scrollable-behavior.md](./02-frontend-scrollable-behavior.md) | Size decoupling + `overflow: auto` scroll region + custom scrollbar in `stack-view.js`/`group-view.js`/`build.js`. |
| 3 | [03-frontend-tests-smoke.md](./03-frontend-tests-smoke.md) | JS unit test (DOM stubs) + browser smoke page. |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Reference docs + branch changelog + full validation. |

## Testing as you go

- Python: `uv run pytest py/tests/viz/test_views.py -q`
- JS unit: `node --test dev/src/js-tests/*.test.mjs`
- JS syntax: `node --input-type=module --check <file>`
- Docs: `uv run mkdocs build --strict`

## Non-goals

- No `ScrollView` node type.
- No change to `SplitView`/`split-resolver.js` (its computed `overflow` stays
  unused, as today).
- No scrollbars for `SceneView`/`ThreeJsView` panes.
- `wrap`-direction stacks keep current behaviour (their content min/preferred is
  already `0`/`null`, so the decoupling is a no-op; `overflow: auto` still
  applies).
