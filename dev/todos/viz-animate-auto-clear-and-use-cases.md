# Animate `auto_clear`, `viz(...)` shorthand, and use-case docs/examples

**Created:** 2026-08-22 | **Status:** Plan

## Goal

1. Fix the two problems in the animation loop: entities never appear (no
   `flush()`), and per-frame `viz.add(...)` calls accumulate objects forever.
   Fix the latter with an `auto_clear` flag on `animate()` that removes objects
   added inside the loop at the start of the next frame.
2. Add a `Visualizer.__call__` shorthand so `viz(point, color=...)` is the same
   as `viz.new(...)` (returns a `VizObjectRef`), making the pre-create + update
   pattern more concise.
3. Restructure the visualizer docs around *use cases* and add Jupyter notebook
   examples under `py/examples/jupyter/`.

## Background (current behaviour)

- `Visualizer.animate(*, fps, stop_key, stop_modifiers, scene_name)` yields once
  per frame and paces to `fps`, but never flushes. Users are expected to call
  `flush()` themselves (per `docs/py/viz/animation.md`), which is easy to forget.
- `viz.add(...)` allocates a fresh 8-char UUID id on every call
  (`Scene.add` → `_generate_id()`), so a loop that calls `add()` per frame keeps
  every frame's objects in the scene.
- `Scene.flush()` pops removed ids from `_objects`/`_nodes` and clears
  `_removed_ids`; `Scene.remove(id)` marks an id for removal (cascading to node
  descendants) and is flushed on the next `flush()`. `_objects` keys therefore
  are the authoritative set of *live* objects (scene entities **and** overlay
  labels) after a flush.
- `viz.new(...)` returns a `VizObjectRef` whose `.entity` setter marks the node
  dirty (so `flush()` sends only changed entities). `VizObjectRef` has no
  `__call__`; `Visualizer` has none either.

## Design decisions

### 1. `animate(auto_clear=False)`

State lives in the generator frame (a local variable), **not** on the
`Visualizer`, so each `animate()` call gets its own baseline and there is no
cross-call leakage — this also sidesteps the "each context manager call creates
a new context" concern that motivated the `viz.block()` idea (we are *not*
adding `viz.block()`).

At the top of every iteration, only when `auto_clear=True`:

1. `flush()` the target scene (push the previous frame's dirty state → fixes
   "no show").
2. On the first iteration, capture `baseline = set(scene._objects.keys())`.
3. On later iterations, `scene.remove(id)` for every live id not in `baseline`
   (marks for removal; flushed together with the frame's additions).

Pseudo-diff in the generator body:

```python
baseline: set[str] | None = None
while not self.interrupted(scene_name):
    if auto_clear:
        self._flush_scene(scene_name)
        scene = self._scenes[scene_name]
        current = set(scene._objects.keys())
        if baseline is None:
            baseline = current
        else:
            for oid in current - baseline:
                scene.remove(oid)
    now = time.monotonic()
    yield now - prev
    prev = now
    ...
```

- `baseline is None` (not "empty set") distinguishes "not captured yet" from a
  legitimately empty scene.
- Diffing `_objects` keys covers entities **and** their labels in one pass
  (labels are overlay objects stored in the same dict), so `viz.add(..., label=...)`
  inside the loop cleans up fully.
- `baseline` is captured *before* the first body runs → anything added before
  the loop persists; everything added inside the loop is cleared each frame.
- Plumb `auto_clear` through `VizSceneHandle.animate()` (which delegates to
  `self._viz.animate(..., scene_name=self._name)`).

### 2. `Visualizer.__call__`

```python
def __call__(self, obj: VizInputType | None = None, **kwargs: Any) -> "VizObjectRef":
    """``viz(obj, ...)`` is shorthand for :meth:`new`."""
    return self.new(obj, **kwargs)
```

Returns a `VizObjectRef`, enabling the concise pattern:

```python
p = viz(Point(3, 0, 0), color="#ff4444")
for dt in viz.animate(fps=30):
    p.entity = Point(...)     # update in place
    viz.flush()
```

### 3. Docs structure

Three new pages inserted directly after the Overview in the `mkdocs.yml` nav,
then the existing files follow (Jupyter stays last as the detailed reference):

- `use-cases-scripts.md` — interactive / animation / export in plain scripts.
- `use-cases-notebooks.md` — interactive (re-run), animation, export in notebooks.
- `app.md` — `VisualizerApp` (most flexible: controls + lifecycle).

Also update `index.md` (topic table + example links), `animation.md`
(document `auto_clear` and `viz(...)`), `visualizer.md` (`viz(...)` shorthand),
and `jupyter.md` (correct animation pattern).

### 4. Notebook examples

New subfolder `py/examples/jupyter/` with:

- `interactive.ipynb` — context manager + idempotent `display()`.
- `animation.ipynb` — Pattern A (`viz(...)` pre-create + `.entity` update) and
  Pattern B (`animate(auto_clear=True)`).
- `export.ipynb` — HTML / glTF / figure export from a notebook.

## Files

- Modify: `py/pytanga/viz/visualizer.py` (`animate(auto_clear=...)`, `__call__`)
- Modify: `py/pytanga/viz/_scene_handle.py` (`animate(auto_clear=...)` passthrough)
- Tests: `py/tests/viz/test_scene_session.py` (or a new `test_auto_clear.py`)
- Add docs: `docs/py/viz/use-cases-scripts.md`, `docs/py/viz/use-cases-notebooks.md`,
  `docs/py/viz/app.md`
- Modify docs: `mkdocs.yml`, `docs/py/viz/index.md`, `docs/py/viz/animation.md`,
  `docs/py/viz/visualizer.md`, `docs/py/viz/jupyter.md`
- Add examples: `py/examples/jupyter/interactive.ipynb`, `animation.ipynb`, `export.ipynb`
- Changelog: append to `docs/changelog/2026-08-22_fix-viz.md`

## Steps

### Phase 1 — `__call__` + `animate(auto_clear=...)`

- [x] Add `Visualizer.__call__(obj, **kwargs)` → `self.new(obj, **kwargs)`.
- [x] Add `auto_clear: bool = False` to `Visualizer.animate` and the
      flush-first / baseline / diff-remove reconcile described above.
- [x] Plumb `auto_clear` through `VizSceneHandle.animate()`.

### Phase 2 — Tests

- [x] `viz(point, color=...)` returns a `VizObjectRef` equal to `viz.new(...)`
      and `.entity` updates mark the node dirty.
- [x] `auto_clear`: baseline captured on first frame; objects added inside the
      loop (incl. labels) are removed on the next frame; pre-loop objects persist;
      an empty scene is handled; scoping respects `scene_name`.
- [x] `auto_clear=False` (default) preserves existing `animate()` behaviour.

### Phase 3 — Docs

- [ ] Add `use-cases-scripts.md`, `use-cases-notebooks.md`, `app.md`.
- [ ] Reorder/insert them in `mkdocs.yml` nav; update `index.md` topic table and
      example links.
- [ ] Update `animation.md`, `visualizer.md`, `jupyter.md` for `auto_clear` and
      the `viz(...)` shorthand.

### Phase 4 — Notebook examples

- [ ] Add `py/examples/jupyter/interactive.ipynb`.
- [ ] Add `py/examples/jupyter/animation.ipynb`.
- [ ] Add `py/examples/jupyter/export.ipynb`.

### Phase 5 — Changelog

- [ ] Append New Features bullets for `animate(auto_clear=...)` and `viz(...)`.

## Notes / edge cases

- **Flush ordering matters.** Flush *before* removing so the previous frame's
  additions actually appear; with a body `flush()` the removal rides along with
  the next frame's additions (no one-frame lag).
- **Groups are not covered.** The diff uses `_objects` (scene entities + labels).
  Group nodes created via `add_group` inside the loop are out of scope; document
  that `add()`/`new()` entities are the supported case.
- **Body `flush()` still recommended.** Even with the top-of-loop flush, a final
  `flush()` in the body guarantees the last frame is pushed before the loop ends.
- **`__call__` vs `add`.** `viz(...)` returns a `VizObjectRef` (like `new`), not
  a `str` id (like `add`). Document this distinction.
