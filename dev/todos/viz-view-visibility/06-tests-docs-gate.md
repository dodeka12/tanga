# Phase 6 — Tests, docs, changelog, gate

**Depends on:** 01–05 | **Status:** Done

## Tests

- `js/dev/tests/helpers/fake-dom.mjs` — minimal DOM (`EventTarget`-based
  element, `classList`, inline `style`, attributes, `ResizeObserver` and
  `getComputedStyle` stubs) so layout views can be driven under `node --test`
  without jsdom.
- `js/dev/tests/view-visibility.test.mjs` — hidden view size/flow contract,
  inline-`display` round-trip, `visibilitychange`, `applyNodeVisibility`
  (absence means visible), hidden children in `stackMinSize`/
  `stackPreferredSize`, plus the `view-state.js` registry/`applyViewState`
  routing and subtree unregistration.
- `js/dev/tests/params-row-visibility.test.mjs` — initial hidden state, runtime
  hide/show, gap-aware `_measureHeight`, unsubscribe on `removeChild`.
- `js/dev/tests/visibility-smoke.mjs` + `serve-visibility-smoke.py` — Playwright
  smoke for the real layout: hidden group takes no space, probe group keeps
  `display:flex`, hidden params row hides its key label, runtime toggles, and a
  hidden group survives a layout re-push and shows again afterwards.
- Python: `test_layout_api.py` (group ids in
  `set_control_visible`/`set_control_enabled`) and `test_params_view.py`
  (`GroupUI(visible/enabled)` reaching the nested group).

## Docs

- `docs/dev/architecture/viz-controls-and-interactions.md` — new
  "Visibility is a view property" subsection under
  "Control enable/disable/hide (`control_state`)": the build funnel, the
  protected size hooks, the `view-state.js` registry, row hiding, and the
  Python fallback to `resolve_group`.
- `docs/changelog/2026/11/13_fix-view-visibility.md` — bug fixes + refactor.

## Gate

```bash
uv run pytest py/tests -q
uv run ruff check py/ tools/ js/dev/tests
uv run ruff format --check py/ tools/ js/dev/tests
uv run mkdocs build --strict
uv run python tools/build-viewer-js.py            # rebuild the bundle
uv run python tools/build-viewer-js.py --check
cd js/dev && npm test && npm run check
```
