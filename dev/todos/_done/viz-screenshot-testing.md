# Headless Browser Screenshot Verification for the Viz Split View

**Created:** 2026-08-24 | **Status:** Planned

## Goal

Verify what the Tanga 3D viewer *actually renders* — specifically the split-view
layout, splitters, and the `GroupView`/control views — by driving a real
browser headlessly, waiting for the WebSocket-driven DOM to settle, and
screenshotting it. This closes the gap left by the split-view work, whose
frontend so far was only validated by unit tests and a WS-level handshake check,
not by looking at pixels.

## Background / analysis

### What the agent can and cannot see

- The VS Code **Simple Browser** is a user-facing webview panel — the agent
  cannot screenshot it or read its DOM, so it is not usable for verification.
- The agent **can** read image files back with its file tools, so a screenshot
  written to disk is inspectable.

### What is available on this machine (verified 2026-08-24)

- **Google Chrome 151** at `/usr/bin/google-chrome` (+ `google-chrome-stable`),
  and **Firefox 153** (snap). No Playwright installed (no `node_modules`, no
  Python package, no `~/.cache/ms-playwright`).
- **Node v22.23.1 / npm 10.9.8** (already used for the pure JS tests).
- Network access to the CDNs (jsdelivr/unpkg) that `viewer.html` uses to load
  Three.js.

### Rendering caveats to plan around

- **WebGL.** Headless Chrome renders WebGL via SwiftShader (software). Recent
  Chrome refuses software WebGL unless launched with `--enable-unsafe-swiftshader`
  (often paired with `--use-angle=swiftshader`). If WebGL context creation fails,
  the viewer already degrades to its `webglOk = false` "headless mode" — meshes
  don't draw but the **DOM still renders** (splitters, panes, control panels),
  which is exactly what the three split-view caveats are about.
- **WebSocket timing.** The page is populated asynchronously after the `ready`
  handshake (`view_layout`, per-scene `scene_config`, `controls_define`). A
  plain "screenshot on `load`" races this; the harness must wait for the layout
  DOM (`.tanga-split`) and the control panel (`.tanga-control-panel`) to exist.

### Approach decision

- **Primary:** Playwright (Node) driving the **already-installed system Chrome**
  via `channel: 'chrome'` — no browser download (`playwright install` is *not*
  needed). This gives reliable waits + full-page/element screenshots.
- **Fallback (zero-install):** raw
  `google-chrome --headless --disable-gpu --screenshot=… --virtual-time-budget=… URL`.
  Simpler but fragile for WS-driven content; keep it only as a smoke path.
- Screenshots go to `dev/tmp/screenshots/` (add `dev/tmp/` to `.gitignore`); the
  agent then reads the PNGs back.

## Files

- `dev/src/viz_screenshot_server.py` — start the `demo_split_view.py` layout
  **without** opening a browser (`Visualizer(open_browser=False)` +
  `set_layout(..., name="demo")` + `start_server(port=…)`), then block.
- `dev/src/screenshot_split_view.mjs` — Playwright script: launch system Chrome
  headless (SwiftShader flags), open `http://localhost:<port>/?view=demo`, wait
  for `.tanga-split` + `.tanga-control-panel`, screenshot full page + pane crops.
- `dev/package.json` — `playwright` devDependency (the repo currently has no
  `package.json`; the pure JS tests use Node's built-in runner without one).
- `.gitignore` — add `dev/tmp/` (screenshots must not be committed).

## Steps

### Phase 1 — Server harness (no browser)

- [ ] Add `dev/src/viz_screenshot_server.py`: build the same scenes + layout as
  `py/examples/viz/demo_split_view.py`, then `set_layout(layout, name="demo")`
  and `start_server(port=18999)` with `open_browser=False`; block until Ctrl+C.
- [ ] Confirm a headless GET of `http://localhost:18999/?view=demo` returns
  `viewer.html` (the `?view=` routing is client-side).

### Phase 2 — Playwright against system Chrome

- [ ] Add `dev/package.json` with `"devDependencies": {"playwright": "<current>"}`;
  run `npm install --prefix dev` (downloads only the Playwright driver, **not** a
  browser).
- [ ] Verify `chromium.launch({ channel: 'chrome', headless: true, args:
  ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'] })` launches Chrome 151.

### Phase 3 — Screenshot script

- [ ] `dev/src/screenshot_split_view.mjs`:
  - launch system Chrome headless with the SwiftShader flags, `viewport` 1400×900;
  - `goto('http://localhost:18999/?view=demo')`;
  - `waitForSelector('.tanga-split')` then `waitForSelector('.tanga-control-panel')`;
  - a short settle wait (renderer/tweens), then `page.screenshot()` of the full
    page plus element screenshots (sidebar, each pane, the splitter bars);
  - write PNGs to `dev/tmp/screenshots/`.

### Phase 4 — Inspect + fix loop

- [ ] Read the PNGs and confirm each item, fixing code as needed and re-running:
  - layout is correct (sidebar left, main top, side+detail bottom);
  - the **vertical splitter sits at ~70%** of the height (not pinned to the
    bottom) — confirms `sizes=[70%, 30%]` is honored;
  - the **fixed sidebar splitter is visually distinct** (transparent) from the
    movable splitters (filled);
  - the **"Actions" panel with two buttons is visible** in the sidebar;
  - scene panes stay at least their 120 px minimum when a splitter is dragged
    (drive the drag via `page.mouse`).

### Phase 5 — Make it repeatable (optional hardening)

- [ ] Add DOM assertions so the check is not eyeball-only: splitter `y` position
  ≈ 0.7×viewport height via `getBoundingClientRect()`; control button count; pane
  min-size after a simulated drag. Keep it a dev script, not a CI gate.

## Verification

- [ ] `uv run python dev/src/viz_screenshot_server.py` starts and serves
  `/?view=demo`.
- [ ] `node dev/src/screenshot_split_view.mjs` produces `dev/tmp/screenshots/*.png`.
- [ ] The screenshots show the five items listed in Phase 4 (or, after Phase 5,
      the assertions pass).

## Non-goals / follow-ups

- Visual-regression baselines / pixel-diffing in CI — out of scope.
- Downloading a Playwright-bundled browser — use the system Chrome.
- Cross-browser (Firefox/Safari) coverage — out of scope.
- Replacing the existing manual viewer checks — this supplements them.

