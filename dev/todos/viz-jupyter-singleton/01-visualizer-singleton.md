# Phase 1 — Jupyter-scoped singleton

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`) for the
> subsystem(s) this work touches, so the new code aligns with the documented
> architecture.  If this work introduces or changes architecture, update the
> developer docs.

## Goal

`Visualizer()` returns the same instance across repeated calls **only** when
running under Jupyter (`_is_jupyter()` is `True`).  Outside Jupyter it keeps
creating independent instances.  Add a `reset()` classmethod for tests/tooling.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- New: `py/tests/viz/test_visualizer_singleton.py`

## Steps

- [x] **1.1 — Add a class-level instance cache + `__new__`**
  - Add `_instance: "Visualizer | None" = None` to the `Visualizer` class body.
  - Add `def __new__(cls, *args, **kwargs)` that returns `cls._instance` when
    `_is_jupyter()` is `True` and it is already set; otherwise create
    `instance = super().__new__(cls)`, cache it (Jupyter only), and return it.
  - `_is_jupyter` is already imported at the top of `visualizer.py`
    (`from ._utils import _is_jupyter`).

- [x] **1.2 — Guard `__init__` with `_initialized`**
  - At the very top of `__init__`, return early when the instance is already
    initialized:
    ```python
    if getattr(self, "_initialized", False):
        return
    ```
  - Set `self._initialized = True` at the end of the normal construction path.

- [x] **1.3 — Add `Visualizer.reset()`**
  - Add a `@classmethod def reset(cls)` that, when `cls._instance` exists and its
    server is running, calls `instance.stop_server()` (guard exceptions), then
    sets `cls._instance = None`.  This lets tests/tooling obtain a fresh
    instance.

- [x] **1.4 — Add singleton tests**
  - In `py/tests/viz/test_visualizer_singleton.py`, add an autouse fixture that
    calls `Visualizer.reset()` before/after each test for isolation.
  - Monkeypatch `pytanga.viz.visualizer._is_jupyter` to return `True`; assert
    `Visualizer() is Visualizer()`.
  - With `_is_jupyter` returning `False`, assert two constructions are distinct
    instances.
  - Assert `reset()` clears the cache so the next construction is fresh.

## Validation

`uv run pytest py/tests/viz/test_visualizer_singleton.py -q`

## Notes

- `_is_jupyter()` is `False` under pytest (no IPython kernel), so the ~313
  existing constructions are unaffected; the singleton is only exercised where
  tests monkeypatch it to `True`.
- Python calls `__init__` even when `__new__` returns a cached instance — hence
  the `_initialized` guard is mandatory.
