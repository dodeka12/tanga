# Phase 5 — Example

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add a runnable example demonstrating determinate + indeterminate progress bars,
a title, and status text.

## Files

- New: `py/examples/viz/ui/controls/progress_bar.py`

## Steps

- [x] **5.1 — Example (`py/examples/viz/ui/controls/progress_bar.py`)**
  - `VisualizerApp` with a `GroupView` overlay holding a determinate
    `ProgressBarView` (title, `total=100`), an indeterminate `ProgressBarView`
    (title, animated), and a `ButtonView` to start.
  - Handler drives both bars in an `asyncio.sleep` loop via `set_progress` /
    `set_text` / `set_indeterminate`.
  - Follow `dev/workflows/example-docs.md`: one-line description, `Run with:`
    line, trailing `Keywords:` line.

- [x] **5.2 — Docs gallery regen**
  - `uv run python tools/generate-example-docs.py` then `--check`.

## Validation

```bash
uv run python -m py_compile py/examples/viz/ui/controls/progress_bar.py
uv run python tools/generate-example-docs.py --check
```
