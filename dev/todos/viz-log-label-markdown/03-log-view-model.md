# Phase 3 — `LogView` backend data model

## Goal

Deliver the pure-Python `LogView` (a plain `View`) with the full data API:
`log()`, `get_log()`, `write_file()`, `load_file()`, `clear()`, FIFO
`max_history`, dict folding, and UTC timestamps — plus serialization and a tree
walk helper.  No frontend yet.

## Files

- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/__init__.py`
- New: `py/tests/viz/test_log_view.py`

## Steps

- [x] **3.1 — Add `LogView` (`views.py`)**
  - `_node_type = "log_view"`; constructor `(id=None, *, max_history=None,
    **kwargs)` with `kwargs.setdefault("min_width", Size.px(200))` and
    `min_height` 120; auto-id `f"log{next(_log_view_counter)}"` (new module
    counter next to `_scene_view_counter`).
  - Store `self.id`, `self.max_history` (validate `None` or non-negative int),
    `self.lines: list[dict]`, and `self._push = None` (callback slot).

- [x] **3.2 — `log()` / `clear()` + history cap**
  - `log(message)`: build `{"time": datetime.now(timezone.utc).isoformat()}`;
    if `message` is a `dict`, `line.update(message)`, else
    `line["message"] = str(message)`.  Append, truncate to the last
    `max_history` entries when set, then call `self._push(self.id, "append",
    [dict(line)])` if `self._push` is set.
  - `clear()`: empty `self.lines`; call `self._push(self.id, "clear")` if set.
  - Import `datetime`/`timezone` at the top of `views.py`.

- [x] **3.3 — `get_log()` / file I/O**
  - `get_log()` → `[dict(line) for line in self.lines]`.
  - `write_file(path)` → write JSON lines (one `json.dumps(line)` per line) via
    `pathlib.Path.write_text(encoding="utf-8")`.
  - `load_file(path)` → read lines, `json.loads` each non-blank line, truncate
    to `max_history`, replace `self.lines`, push `("replace", lines)` if set.
  - Import `json` and `pathlib.Path` at the top of `views.py`.

- [x] **3.4 — Serialize + tree walk + export**
  - `_serialize`: `super()._serialize(...)` then set `result["id"] = self.id`
    (stable, like `SceneView`/`ControlView`), `result["max_history"]`,
    `result["lines"] = [dict(l) for l in self.lines]`.
  - Add `iter_log_views(root)` (DFS over `children`/`overlay`, mirroring
    `iter_control_views`).
  - Add `LogView` to `views.py __all__`; import/export `LogView` in
    `__init__.py`.

- [x] **3.5 — Tests (`test_log_view.py`)**
  - `log("x")` → line `{"time": <iso str>, "message": "x"}`.
  - `log({"message": "hi", "level": "info"})` → `time` + `message` + `level`
    (keys folded).
  - `max_history=2` drops the oldest; `None` keeps all.
  - `get_log()` returns copies (mutating the result does not change the view).
  - `write_file`/`load_file` round-trip (tmp_path); `load_file` truncates to
    `max_history`.
  - `serialize_layout(LogView(...))` emits `type == "log_view"`, `id`,
    `max_history`, `lines`.

## Validation

```
uv run pytest py/tests/viz/test_log_view.py py/tests/viz/test_views.py -q
```

## Notes

- `time` is a UTC ISO-8601 string with microseconds — sortable and JSON-safe.
- `_push` is deliberately unset until Phase 5; `log()`/`clear()` must no-op
  cleanly when it is `None`.
