# Phase 2 — Style defaults holder (`VizStyleDefaults`)

**Status:** Planned

## Goal

Bundle all per-kind and global default style instances into a single,
copyable `VizStyleDefaults` object so that:

- the `Visualizer` owns one canonical instance, and
- each `Scene` receives a **copy** at creation (per-scene default changes
  never leak back to the Visualizer).

This phase refactors **configuration ownership only**: it changes where the
defaults live and how `Scene` acquires them. It does **not** introduce the
scene-graph node classes, does **not** change serialization, and does **not**
re-wire where style resolution happens.

## Scope boundary (important)

- **Done here:** a deep-copyable holder, the `Visualizer` forwarding to it
  through the existing `_default_*` attributes, and `Scene` holding its own
  independent copy with accessor properties.
- **Deferred to Phase 3/4:** making style resolution read from the `Scene`'s
  own holder instead of the `Visualizer`'s. Only once `Scene.add` /
  `Scene.add_label` resolve styles from `self.style_defaults` (Phase 3) and
  `Scene.flush` serializes from node-resolved styles (Phase 4) does the
  downstream "no propagation" snapshot behavior become observable.

## Files

- New: `py/pytanga/viz/_style_defaults.py`
- Modify: `py/pytanga/viz/visualizer.py`
- Modify: `py/pytanga/viz/scene.py`

## Key decisions

- **Snapshot copy.** `Scene` holds a **copy** of the Visualizer's defaults
  captured at scene creation. Mutating a scene's holder never affects the
  Visualizer (or other scenes). The reverse direction — later Visualizer
  mutations not affecting an existing scene — becomes observable in
  Phase 3/4 once resolution reads the scene's holder.
- **Bundled contents.** The holder owns the styles that participate in scene
  object/label resolution:
  - per-kind entity/operator styles (`Visualizer._default_styles`),
  - global label style + per-kind label styles
    (`_default_label_style`, `_default_label_styles`),
  - global annotation style (`_default_annotation_style`),
  - global texture label style + per-kind texture label styles
    (`_default_tex_label_style`, `_default_tex_label_styles`).
- **Out of scope.** `ActPointStyle`, figure style, and animation style are
  not part of scene-node style resolution and remain owned directly by the
  Visualizer / exporter.
- **Deep copy.** `copy()` must deep-copy each bundled style instance so scenes
  are fully independent.

## Steps

### `_style_defaults.py`

- [ ] `@dataclass class VizStyleDefaults` with fields:
      `default_styles`, `default_label_style`, `default_label_styles`,
      `default_annotation_style`, `default_tex_label_style`,
      `default_tex_label_styles`.
- [ ] `make_defaults()` factory that builds a fresh canonical instance from the
      existing `_make_default_*` factory functions in `_style_dict.py`.
- [ ] `copy(self) -> VizStyleDefaults` deep-copying every field (via
      `copy.deepcopy`).
- [ ] No import of `Visualizer`/`Scene` (avoid circular imports); import the
      `_style_dict` factories only inside `make_defaults()`, and style types
      under `TYPE_CHECKING`.

### `visualizer.py`

- [ ] Replace the individual `_default_*` attributes with a single
      `self._style_defaults: VizStyleDefaults` built via `make_defaults()`.
- [ ] Keep `self._default_styles` (and the other `_default_*`) as read-only
      properties forwarding to `self._style_defaults`, so the existing public
      API (`viz.default_styles`, `viz.default_label_style`, …) and internal
      uses keep working unchanged.
- [ ] Drop the now-unused `_make_default_*` imports.
- [ ] `self._default_act_point_style` stays on the Visualizer (not bundled).
- [ ] When constructing the main `Scene` and each named `Scene`, pass
      `style_defaults=self._style_defaults.copy()`.
- [ ] Leave `_flushed_scene` / `_full_state_for` / label resolution untouched
      (they still read the Visualizer's `_default_*` properties this phase).

### `scene.py`

- [ ] Add `Scene(..., style_defaults: VizStyleDefaults | None = None)`; when
      `None`, fall back to `make_defaults()` (standalone `Scene()` usage
      keeps working).
- [ ] Store `self.style_defaults`.
- [ ] Expose read-only accessor properties (e.g. `default_styles`,
      `default_label_style`, `default_label_styles`, `default_annotation_style`,
      `default_tex_label_style`, `default_tex_label_styles`) reading from
      `self.style_defaults`.
- [ ] Do **not** change `flush` / `full_state` / `add` / `add_label` yet.

## Unit tests

File: `py/tests/viz/test_style_defaults.py`.

- [ ] `test_make_defaults_has_all_fields` — every field is populated.
- [ ] `test_copy_is_deep` — mutating a copied nested style does not affect the
      original.
- [ ] `test_scene_receives_independent_copy` — mutating a scene's holder does
      not change the Visualizer's holder, and vice versa.
- [ ] `test_scene_default_fallback` — `Scene()` without an explicit holder
      gets an independent default holder.
- [ ] `test_visualizer_backcompat_properties` — `viz.default_styles`,
      `viz.default_label_style`, `viz.default_label_styles`,
      `viz.default_annotation_style`, `viz.default_tex_label_style` forward to
      the holder and still expose the pre-existing shapes
      (`viz.default_styles[Point]` works, `viz.default_label_styles` is a
      `_StyleDict`).

## Verification

- [ ] `uv run pytest py/tests/viz/test_style_defaults.py py/tests/viz/test_scene_session.py` passes.
- [ ] `viz.default_styles[Point]` still works through the backward-compat property.
- [ ] Mutating a scene's holder never changes the Visualizer's holder.
- [ ] `Scene()` (standalone) still constructs with an independent holder.
- [ ] Existing viz tests (serializer, controls, 2d, interaction, export) still pass.