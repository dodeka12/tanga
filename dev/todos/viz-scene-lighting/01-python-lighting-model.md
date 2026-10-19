# Phase 1 — Python lighting model + `SceneConfig.lighting`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the "Scene config" section) so the
> new `SceneConfig.lighting` field and its serialization match the documented
> scene-config contract.  This phase only *adds* data + serialization; it does
> not change architecture (the wire `scene_config` message already exists).

## Goal

Add a `SceneLighting` value object (ambient + directional lights), a canonical
default that mirrors the current hardcoded frontend lights, and a
`SceneConfig.lighting` field that serializes into the `scene_config` message.

## Files

- **New** `py/pytanga/viz/_lighting.py` — `LightSpec`, `DirectionalLightSpec`,
  `SceneLighting`, `DEFAULT_SCENE_LIGHTING`.
- **Edit** `py/pytanga/viz/scene.py` — add `SceneConfig.lighting` + `to_dict` branch.
- **Edit** `py/pytanga/viz/__init__.py` — export `SceneLighting`, `LightSpec`,
  `DirectionalLightSpec`.
- **New** `py/tests/viz/test_scene_lighting.py`.

## Steps

- [x] 1.1 Create `py/pytanga/viz/_lighting.py`:
  - `@dataclass(frozen=True) class LightSpec` with `color: str = "#ffffff"`,
    `intensity: float = 1.0`.
  - `@dataclass(frozen=True) class DirectionalLightSpec(LightSpec)` adding
    `direction: tuple[float, float, float] = (0.0, 0.0, 1.0)` (unit vector
    pointing **toward** the light; frontend normalizes).
  - `@dataclass(frozen=True) class SceneLighting` with
    `ambient: LightSpec = field(default_factory=...)` and
    `lights: tuple[DirectionalLightSpec, ...] = field(default_factory=...)`.
  - `DEFAULT_SCENE_LIGHTING` mirroring `three-view.js::_addDefaultLights`:
    ambient `#ffffff` @ `0.5`; directionals `normalize((10,20,10))` @ `0.8` and
    `normalize((-5,-2,-8))` @ `0.3` (store pre-normalized components).
  - `SceneLighting.to_dict()` → `{"ambient": {color, intensity}, "lights": [{direction: [x,y,z], color, intensity}]}`.
- [x] 1.2 Add `lighting: SceneLighting | None = None` to `SceneConfig` (after
  `keyboard`).  In `SceneConfig.to_dict()`, emit `result["lighting"] =
  self.lighting.to_dict()` only when `self.lighting is not None`.
- [x] 1.3 Export `SceneLighting`, `LightSpec`, `DirectionalLightSpec` from
  `py/pytanga/viz/__init__.py` (import + `__all__`), matching existing export style.
- [x] 1.4 Add `py/tests/viz/test_scene_lighting.py`:
  - default `SceneLighting` `to_dict()` matches the documented wire shape and
    values (ambient 0.5, two directionals).
  - `SceneConfig()` with `lighting=None` omits the `lighting` key.
  - `SceneConfig(lighting=custom)` includes the `lighting` block verbatim.
  - `DirectionalLightSpec` accepts a non-normalized direction and keeps it as-is
    (normalization is the frontend's job).

## Validation

```bash
uv run pytest py/tests/viz/test_scene_lighting.py -q
```
