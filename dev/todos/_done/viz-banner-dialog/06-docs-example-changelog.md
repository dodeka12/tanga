# Phase 6 — Docs, example, changelog, full validation

## Goal

Document and exemplify the banner API; update the changelog; run the full
suite.

## Steps

- [x] **6.1 — Docs**
  - New `docs/py/viz/visualizerapp/banners.md` covering: the four banner kinds
    (acknowledge / options / yes-no-cancel / modal), alignment semantics,
    global vs per-scene, `auto_hide` / `dismissable`, KaTeX text, backend
    removal, and the handler recipe (`show_banner_async` + `submit_user(work,
    done=cleanup)` + `remove_banner` + `flush_async`). Add a "Banners" entry to
    `mkdocs.yml` nav (under VisualizerApp) and link the two examples.
  - Add `show_banner` / `alert` / `confirm` / `remove_banner` / `clear_banners`
    rows to `docs/py/viz/visualizer/visualizer.md`.

- [x] **6.2 — Slider `press`/`release` events (prerequisite for the heavy-work example)**
  - The slider already flushes a final `control:change` on release, but drag
    also emits throttled `control:change` ticks — indistinguishable on the
    backend. Add two distinct lifecycle messages from `createSlider`:
    `control:press` on `pointerdown` (start of the drag) and
    `control:release` on `change` (release). This is possible because the
    slider already listens for `pointerdown` (to stop orbit-control
    propagation).
  - Add `Slider.on_press` / `Slider.on_release` and
    `Visualizer.add_slider(..., on_press=..., on_release=...)` (registered like
    `on_change`), and `control:press` / `control:release` branches in
    `server.py` + `_dispatch_control_event`, so a handler can react to the
    start and end of a drag (e.g. trigger heavy work only on release).

- [x] **6.3 — Examples (`py/examples/viz/banners/`, new)**
  - `banner_types.py` — a plain `Visualizer` script demonstrating every banner
    kind: `alert(...)` (acknowledge), `show_banner(controls=[...])` (custom
    options), `confirm(...)` (yes/no/cancel), and a modal
    `show_banner(dismissable=False)` — plus `align_x`/`align_y` placement,
    KaTeX text, and `remove_banner`/`clear_banners`.
  - `heavy_work.py` — a `VisualizerApp` with a slider whose `on_release`
    handler shows a modal "Calculating…" banner, then fire-and-forgets a 3 s
    dummy compute (`asyncio.to_thread(time.sleep, 3)`) onto the user loop with
    a one-shot `done` callback that updates the scene, `remove_banner`, and
    `flush`.

- [x] **6.4 — Changelog**
  - Append a "Banners" bullet (and a "slider press/release events" bullet) to
    `docs/changelog/2026-08-26_feat-small-extensions.md`.

- [x] **6.5 — Full validation**
  - `uv run pytest -q` (full suite) + `uv run ruff check` on touched Python.

## Validation

`uv run pytest -q && uv run ruff check py/pytanga/viz/`
