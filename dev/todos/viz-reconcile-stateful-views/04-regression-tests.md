# Phase 4 — Log-view re-push regression tests

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add a regression test that reproduces the reported scenario — a stable-id
`LogView` re-pushed via `set_layout(...)`, then `.log()` after the re-push — and
asserts the new line actually renders.  This is the end-to-end gate for the fix
in Phase 1.

## Files

- New: `js/dev/tests/serve-log-smoke.py`
- New: `js/dev/tests/log-view-smoke.mjs`
- Edit: `py/tests/viz/test_log_view.py` (optional backend-side guard)

## Steps

- [x] **4.1 — Smoke server (`js/dev/tests/serve-log-smoke.py`)**
  - Mirror `js/dev/tests/serve-smoke.py`: build a layout with
    `LogView(id="solver_log", max_history=200)`, a toolbar button whose handler
    (a) re-pushes the layout with the same `LogView` id but a changed sibling
    (e.g. add/remove a `LabelView` or toggle a slider), and (b) calls
    `log_view.log("after re-push")`.
  - Serve on a free port without opening a browser and print `SMOKE_URL=…`,
    then `viz.wait()`.

- [x] **4.2 — Playwright smoke (`js/dev/tests/log-view-smoke.mjs`)**
  - Mirror `js/dev/tests/reconcile-smoke.mjs` (headless Chromium, collect
    console errors).  Load `/?view=<name>`, click the re-push button, then assert
    the `.tanga-message-view` pane contains the `"after re-push"` row.
  - Keep a browser-console error assertion so the silent-drop symptom (no error,
    no line) can't regress.

- [x] **4.3 — Backend-side guard (`py/tests/viz/test_log_view.py`)**
  - Add a test using the existing `_FakeServer` / `_patch_push` pattern: create a
    `LogView(id="log0")` in a layout, call `viz.set_layout(...)` twice, then
    `log_view.log("after")`, and assert a `log_update` with action `append` is
    still emitted after the second re-push.
  - Note: this guards the backend push path only; the frontend registry race is
    covered by the Playwright smoke in 4.2 (it cannot be reproduced Python-side).

- [x] **4.4 — Group collapse round-trip smoke**
  - Extend the smoke layout with a `GroupView(id="g1", collapsed=True)`; after the
    re-push, assert the group is still collapsed (`.tanga-group-content` hidden),
    covering the Phase 2/3 group preservation end-to-end.
  - Note: backend `set_collapsed`/`on_toggle` unit tests live in Phase 2 (2.6).

## Validation

```
uv run python js/dev/tests/serve-log-smoke.py          # terminal 1 (prints SMOKE_URL)
node js/dev/tests/log-view-smoke.mjs <printed-url>     # terminal 2
uv run pytest py/tests/viz/test_log_view.py -q
```

> The Playwright smoke is a manual, non-CI gate (needs a live server + Chromium);
> `pytest` and the `node --test` suite are the automated gates.

## Notes

- The existing `serve-smoke.py` scenario is about scene-pane reuse; keep this new
  pair focused on the log-view registry race so it maps 1:1 to the bug report.
- If `LogView` cannot be driven from a button handler (backend control flow),
  trigger the re-push + `log()` from the handler exactly as the report's
  `fpk-viz` app does.
