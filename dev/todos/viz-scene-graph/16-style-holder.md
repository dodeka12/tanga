# Phase 16 — Unified style holder (`VizStyles`)

**Parent:** [README.md](./README.md)
**Status:** Planned

## Goal

Fix the default-style API so that mutating a scene's style defaults actually
affects that scene, by replacing the flat `default_*` property surface with a
single holder class, `VizStyles`, that groups **all seven** changeable style
bundles. The `Visualizer` exposes two accessors:

- `viz.styles` — the holder for the **main scene** (what gets rendered).
- `viz.global_styles` — the **master template** that newly-created scenes copy.

`VizStyles` also gets `__getitem__`/`__setitem__` sugar so the common case is
`viz.styles[Point] = PointStyle(...)` (entity/operator default), while the
other bundles stay addressable by name (`viz.styles.label_kind[Point] = ...`).

## Current state (problem)

- The `Visualizer` owns a **canonical** `VizStyleDefaults` holder
  (`self._style_defaults`); every `Scene` receives a **deep copy** at
  construction (`style_defaults=self._style_defaults.copy()`).
- `Visualizer.default_styles` and friends point at the **canonical**, so
  mutating them has no effect on the already-created main scene (confirmed:
  `viz.default_styles["Line"] = ...` does not change a newly added line).
- Resolution is split inconsistently: **entity** styles resolve from the
  **scene's copy** (`Scene._make_scene_node`), while **label / annotation /
  tex-label** styles resolve from the **canonical** (`_add_to_scene`,
  `set_annotation`). Line length / label anchors also read the canonical.
- Public surface to remove: `default_styles`, `default_label_style` (+setter),
  `default_label_styles`, `default_annotation_style`, `default_act_point_style`
  (+setter), `default_tex_label_style` (mis-named — currently returns the
  per-kind dict), plus the `_default_*` backing properties.

## Design

### `VizStyles` (new module `py/pytanga/viz/_viz_styles.py`)

```python
@dataclass
class VizStyles:
    kind: _StyleDict            # per-kind entity/operator styles
    label_base: LabelStyle      # global label style
    label_kind: _StyleDict      # per-kind label styles
    annotation: AnnotationStyle
    tex_label_base: TextureLabelStyle
    tex_label_kind: _StyleDict  # per-kind texture-label styles
    act_point: ActPointStyle    # global active-point style (folded in)

    def __getitem__(self, key):
        return self.kind[key]

    def __setitem__(self, key, value):
        self.kind[key] = value

    def copy(self) -> "VizStyles":
        ...  # deepcopy every member
```

- `kind` / `label_kind` / `tex_label_kind` are `_StyleDict`, so string keys
  and class keys both work (`viz.styles.kind["Line"]` / `viz.styles[Line]`).
- `make_styles()` builds a fresh canonical instance (renamed from
  `make_defaults()`); it wraps the plain-dict label/tex-label factories in
  `_StyleDict` to normalize the dict members.
- Add `_make_default_act_point_style()` in `_style_dict.py` (moved out of
  `Visualizer.__init__`, currently `hover_emissive="#ffff44", hover_scale=1.5`).

### Old → new mapping

| Old (`Visualizer` / `Scene` property) | New access |
|---|---|
| `default_styles` | `viz.styles.kind` (or `viz.styles[kind]`) |
| `default_label_style` | `viz.styles.label_base` |
| `default_label_styles` | `viz.styles.label_kind` |
| `default_annotation_style` | `viz.styles.annotation` |
| `default_tex_label_style` (mis-named, was per-kind) | `viz.styles.tex_label_kind` |
| (not exposed) | `viz.styles.tex_label_base` |
| `default_act_point_style` | `viz.styles.act_point` |

### Accessors

- `Visualizer.global_styles` → `self._global_styles` (master holder).
- `Visualizer.styles` → `self._scenes[""].styles`.
- `Scene.styles` → its holder (rename of the `style_defaults` attribute).
- `VizSceneHandle.styles` → `self._scene().styles`.

### Resolution fix (the actual bug)

Label / tex-label / annotation / line-length resolution must read the
**scene's** holder (`scene.styles.*`), not the canonical `self._default_*`:

- `_add_to_scene`: label style (≈474-478), tex-label style (≈402-407),
  `resolve_line_length` (≈483-487).
- `set_annotation` (≈609-610).
- `Scene.update_label` / `_make_scene_node` already read the scene holder
  (rename `self.default_styles` → `self.styles.kind`).

## Implementation steps

Ordering rationale: each step *produces* something the next steps *consume*;
no later step revisits earlier work. Step 1 is additive so the tree stays
green until the atomic migration in Step 2.

### Step 0 — Revert the mistaken cylinder-default edits

The working tree still contains four mistaken edits from an earlier attempt
(they changed the *global* line default, which must stay `LineStyle`).

- [x] Revert to `HEAD`: `py/pytanga/viz/_styles/__init__.py` (Line entry),
      `py/pytanga/viz/serializer.py` (`builtins`), `py/tests/viz/test_node_serialization.py`,
      `py/tests/viz/test_serializer.py`.
- [x] Verify: `uv run pytest py/tests/viz -q` green.

### Step 1 — Introduce `VizStyles` (additive, nothing else changes)

- [x] New `py/pytanga/viz/_viz_styles.py`: the `VizStyles` dataclass
      (7 members, `__getitem__`/`__setitem__`, deep `copy()`) and
      `make_styles()` (reusing the existing `_make_default_*` factories;
      wrap `label_kind`/`tex_label_kind` in `_StyleDict`).
- [x] `py/pytanga/viz/_style_dict.py`: add `_make_default_act_point_style()`.
- [x] `py/pytanga/viz/__init__.py`: export `VizStyles`.
- [x] New `py/tests/viz/test_viz_styles.py`: member access, class-key + string-key
      `__getitem__`/`__setitem__`, `copy()` deep isolation, `act_point` default.
- [x] Verify: new tests + full suite green (old API untouched).

### Step 2 — Migrate the library to `VizStyles` (atomic clean break)

- [x] `py/pytanga/viz/visualizer.py`:
      - `self._style_defaults = make_defaults()` → `self._global_styles = make_styles()`;
        drop the inline `ActPointStyle` construction.
      - Add `global_styles` and `styles` properties.
      - Delete all `_default_*` (≈1837-1864) and `default_*` (≈1867-1929)
        properties.
      - `set_default_color` → mutate `self.styles.kind[key]`.
      - `_add_to_scene` + `set_annotation` → read `scene.styles.*`
        (label_base / label_kind / tex_label_base / tex_label_kind /
        annotation / kind) instead of `self._default_*`.
      - `_full_state_for` (≈705) and the export path (≈1815) →
        `styles_map=scene.styles.kind`.
- [x] `py/pytanga/viz/scene.py`:
      - rename the `style_defaults` attribute → `styles` (update `__init__`
        and every `self.style_defaults` reference).
      - `default_*` properties (≈498-525) → `styles.*` members (or remove the
        wrappers and read members directly in `_make_scene_node` /
        `_make_overlay_node` / `update_label`).
- [x] `py/pytanga/viz/_scene_handle.py`: replace `default_styles`,
      `default_label_style`, `default_label_styles`, `default_annotation_style`,
      `default_act_point_style` (≈72-99) with a single `styles` property →
      `self._scene().styles`.
- [x] `py/pytanga/viz/_active.py`: `viz_handle.default_act_point_style` →
      `viz_handle.styles.act_point` (≈255, 257).
- [x] Delete `py/pytanga/viz/_style_defaults.py`.
- [x] Verify: `uv run python -c "import pytanga.viz"` clean; `compileall` on the
      package. (Tests referencing the old API fail until Step 3.)

### Step 3 — Update tests and non-demo examples (clean-break fallout)

- [x] `py/tests/viz/test_style_defaults.py` → rework as the `VizStyles` holder
      test (or fold into `test_viz_styles.py`); the independence assertion now
      becomes: `viz.styles` is the main scene's holder, `viz.global_styles` is
      independent, and named scenes get their own copies.
- [x] `py/tests/viz/test_scene_session.py` (≈442-464, 547-650, 870-912),
      `py/tests/viz/test_imaginary_styles.py` (≈23, 128-345),
      `py/tests/viz/test_node_serialization.py` (≈216),
      `py/tests/viz/test_tex_label_style.py`: replace `default_*` /
      `set_default_color` references with the new accessors.
- [x] Examples: `demo_custom_defaults.py` (and any `demo_tex_label_*.py`,
      `demo_labels.py`) using `default_*` / `set_default_color` → new accessors.
      Also `demo_camera_2d.py`, the exporter (`_exporter.py`), and docstrings in
      `geometry/entities/{circle,point_pair,sphere}.py`.
- [x] Add behavior tests: `viz.styles["Line"] = ...` changes a subsequently
      added line on the main scene; `viz.global_styles` only affects newly
      created scenes; `viz.scene("x").styles` is independent.
- [x] Verify: `uv run pytest py/tests/viz -q` green.

### Step 4 — Demo: cylinder lines in `demo_act_point.py`

- [x] After `viz = Visualizer(...)`, add
      `viz.styles["Line"] = CylinderLineStyle(...)` (before the projection
      lines are first created).
- [x] Verify: syntax + a quick serialize check that a line resolves
      `style_type == "CylinderLineStyle"`.

### Step 5 — Docs

- [ ] `docs/py/viz/styles.md`: replace `viz.default_styles[...]` examples with
      `viz.styles[...]` / `viz.styles.kind[...]`; document `styles` vs
      `global_styles`.
- [ ] `docs/py/viz/labels.md`, `docs/py/viz/texture-labels.md`: any
      `default_label_style` / `default_tex_label_style` references.
- [ ] `docs/py/viz/visualizer.md`: method table + non-blocking-mode examples
      (and any `set_default_color` mentions).
- [ ] `docs/py/viz/scene-graph.md`: if it references `default_styles`.

### Step 6 — Changelog

- [ ] `docs/changelog/2026-08-17_13b30f7.md` (still unreleased — editable):
      add **Breaking Changes** (old `default_*` API removed; `set_default_color`
      now targets the main scene) and **New Features** (`VizStyles`,
      `styles`/`global_styles`, `viz.styles[Kind] = ...` sugar) bullets.
- [ ] `docs/changelog/index.md`: extend the `## [Since 0.9.2]` summary line.

## Verification (end-to-end)

- [ ] `uv run pytest py/tests/viz -q` green.
- [ ] `uv run ruff check py/pytanga/viz py/tests/viz py/examples/viz` — no new
      issues (pre-existing E402/F821/F401 in `visualizer.py` /
      `test_scene_session.py` are out of scope).
- [ ] Manual: `viz.styles["Line"] = CylinderLineStyle(...)` changes a new
      line's render; `viz.global_styles` affects only new scenes; a named
      scene's `styles` are independent.


