# Phase 11 — Scene Export (HTML + glTF)

**Prerequisites:** Phase 8 (integration/polish), Phase 5 (per-entity JS renderers), Phase 4c (style hierarchy)

**Goal:** Add static export capabilities to the `Visualizer` so that a fully interactive 3D scene can be saved to a portable file — either a **self-contained HTML file** (double-click to view) or a **glTF 2.0 binary** (`.glb`) file (openable in any 3D tool, browser, or AR viewer). Both formats work without a running Python server.

---

## 1. Motivation

### 1.1 Use Cases

- Share a visualization with a colleague who doesn't have `pytanga` installed.
- Publish an interactive figure alongside a paper (supplementary material).
- Export to Blender/Unity/Unreal for further artistic rendering.
- Archive a scene snapshot that can be viewed years later without Python.

### 1.2 Two Complementary Formats

| Format | File | Viewer Needed | Best For |
|--------|------|---------------|----------|
| **Self-contained HTML** | `scene.html` | Any modern browser (double-click) | Quick sharing, no-install viewing, embedding |
| **glTF 2.0 Binary** | `scene.glb` | Three.js, Blender, `<model-viewer>`, macOS Preview, Sketchfab | 3D tool interoperability, AR, long-term archival |

---

## 2. Self-Contained HTML Export

### 2.1 How It Works

1. `Visualizer.export_html(path)` serializes the current scene via `Scene.full_state(defaults=...)`.
2. The entity JSON data is embedded directly in a `<script>window.__TANGA_SCENE__ = [...]</script>` tag.
3. The HTML includes CDN imports for Three.js, OrbitControls, and CSS2DRenderer.
4. A minimal bootstrap script reads `__TANGA_SCENE__`, calls the same `createEntityMesh()` / `createOperatorMesh()` functions from Phases 5/6, and sets up the renderer + orbit controls.

### 2.2 Template Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tanga 3D Viewer — Export</title>
  <style>
    body { margin: 0; overflow: hidden; background: #1a1a2e; font-family: sans-serif; }
    #info { position: absolute; bottom: 10px; right: 10px; color: #888; font-size: 12px; }
  </style>
</head>
<body>
  <div id="container"></div>
  <div id="info">Tanga 3D Scene</div>

  <!-- Three.js CDN -->
  <script type="importmap">
    {
      "imports": {
        "three": "https://cdn.jsdelivr.net/npm/three@0.170/build/three.module.js",
        "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170/examples/jsm/"
      }
    }
  </script>

  <!-- Embedded scene data -->
  <script type="application/json" id="tanga-scene-data">
    __SCENE_DATA_JSON__
  </script>
  <script type="application/json" id="tanga-scene-config">
    __SCENE_CONFIG_JSON__
  </script>

  <!-- Bootstrap -->
  <script type="module">
    // __BOOTSTRAP_JS__
  </script>
</body>
</html>
```

### 2.3 Bootstrap Script (inlined, ~80 lines)

The bootstrap script handles:

1. Parse `#tanga-scene-data` and `#tanga-scene-config`.
2. Set up `THREE.Scene`, `PerspectiveCamera`, `WebGLRenderer`, `OrbitControls`, `CSS2DRenderer`.
3. Apply background color, fog, grid from scene config.
4. Iterate over all entities, call `createEntityMesh()` or `createOperatorMesh()`.
5. Register labels (CSS2D objects).
6. If camera config is present, apply it; otherwise auto-fit from entity bounds.
7. Start render loop.

The per-entity renderer logic (`createPoint()`, `createLine()`, etc.) is **copied into the bootstrap script** — no separate module files, since the HTML must be self-contained. This is a maintenance trade-off: the renderers live in `factory.js` for the live server and are duplicated in `export_html()` for self-contained files. The duplication is acceptable because the export is a snapshot — the renderer code at export time is what matters.

### 2.4 Python API

```python
# In visualizer.py

def export_html(self, path: str | Path) -> None:
    """Export the current scene as a self-contained HTML file.

    The resulting file can be opened by double-clicking — no Python
    server, no internet connection needed (Three.js loads from CDN
    by default; set ``offline=True`` to embed a local Three.js bundle).

    Args:
        path: Output file path (e.g., ``"scene.html"``).
    """
    entities = self._scene.full_state(defaults=self._defaults)
    scene_config = self._config.to_dict()
    html = _render_export_html(entities, scene_config)
    with open(path, "w") as f:
        f.write(html)
```

### 2.5 What's Included

- All entity and operator meshes with correct geometry, colors, opacity, and style data.
- Camera (auto-fit or explicit from `CameraConfig`).
- Orbit controls (rotate, pan, zoom).
- Grid and axes (if enabled in `SceneConfig`).
- Labels (CSS2D text overlaid on entities).
- Background color.

### 2.6 What's NOT Included

- No WebSocket connection — static snapshot only.
- No live updates / animation / timeline.
- No MV analysis — only the resolved entity shapes.
- No server-side interaction.

---

## 3. glTF 2.0 Binary (`.glb`) Export

### 3.1 How It Works

1. Build a temporary Three.js scene graph the same way the live viewer does.
2. Use Three.js's `GLTFExporter` to serialize the graph to glTF 2.0 binary format.
3. Write the resulting `ArrayBuffer` to a `.glb` file.

The key insight: **this runs in Python, not in the browser.** We don't actually need a browser to produce the Three.js scene graph — we can skip Three.js entirely and write glTF directly.

### 3.2 Python-Native glTF Writing

Since glTF is a JSON-based format (the binary `.glb` is a JSON header + binary buffer), we can write it directly from Python without needing a JS runtime:

```python
def export_glb(self, path: str | Path) -> None:
    """Export the current scene as a glTF 2.0 binary (.glb) file.

    The resulting file can be opened in Blender, macOS Preview,
    Windows 3D Viewer, 〈model-viewer〉, or any glTF-compatible tool.

    Args:
        path: Output file path (e.g., ``"scene.glb"``).
    """
    from ._gltf import build_gltf_scene

    entities = self._scene.full_state(defaults=self._defaults)
    glb_data = build_gltf_scene(entities, self._config)
    with open(path, "wb") as f:
        f.write(glb_data)
```

### 3.3 glTF Scene Structure

A new module `py/pytanga/viz/_gltf.py` translates our entity JSON to glTF nodes:

| Entity Kind | glTF Node |
|-------------|-----------|
| Point, HPoint | `mesh` with a sphere primitive (radius → scale) |
| Direction | `mesh` with cylinder + cone primitives in a node group |
| Line | `mesh` with cylinder primitive, oriented to direction vector |
| Plane | `mesh` with plane primitive (double-sided), oriented to normal |
| Circle | `mesh` with torus primitive (or high-res ring), oriented to normal |
| Sphere | `mesh` with sphere primitive + optional wireframe edges |
| Space | `mesh` with box edges (line list) |
| PointPair | Two sphere primitives + cylinder connector |
| Rotor | Ring mesh + axis line + arc |
| Translator | Cylinder + cone arrow |
| Dilator | Multiple torus rings |
| Motor | Tube (helix curve) + axis line |
| Reflection | Plane + short arrow |
| Inversion | Wireframe sphere + crosshair |
| GeneralRotor | Two disc meshes + axis line |
| GeneralDilator | Rings + arrow |

Each entity's `style` dict (from Phase 4c) maps to glTF material properties:
- `style.size` → node scale
- `style.thickness` / `style.tube_radius` → primitive geometry parameters
- `color` → `pbrMetallicRoughness.baseColorFactor`
- `opacity` → material alpha

### 3.4 glTF Material Mappings

| Tanga Property | glTF PBR Material |
|----------------|-------------------|
| `color` (hex) | `pbrMetallicRoughness.baseColorFactor` (RGBA) |
| `opacity` | `pbrMetallicRoughness.baseColorFactor[3]` |
| `wireframe: true` | No glTF native wireframe — approximate with edges or thin cylinders |
| translucent planes | `alphaMode: "BLEND"`, `doubleSided: true` |

### 3.5 `<model-viewer>` Compatibility

Google's `<model-viewer>` web component provides one-line glTF viewing:

```html
<model-viewer src="scene.glb" camera-controls auto-rotate></model-viewer>
```

This works with any `.glb` file — no rendering code needed on the recipient's side. We should document this as the recommended way for recipients to view exported `.glb` files.

---

## 4. File Structure

### 4.1 New Files

| File | Content |
|------|---------|
| `py/pytanga/viz/_export.py` | `_render_export_html()` — renders the HTML template with embedded scene data and bootstrap JS |
| `py/pytanga/viz/_gltf.py` | `build_gltf_scene()` — builds glTF 2.0 binary from entity list + scene config |
| `dev/src/test_export_smoke.py` | Smoke test that exports both formats and checks file validity |

### 4.2 Modified Files

| File | Changes |
|------|---------|
| `py/pytanga/viz/visualizer.py` | Add `export_html()` and `export_glb()` methods |
| `py/pytanga/viz/__init__.py` | No new exports needed (methods on `Visualizer`) |
| `py/pytanga/viz/templates/viewer.html` | Unchanged — export uses its own template, not the live viewer |

---

## 5. Cross-Cutting Concerns

### 5.1 Renderer Code Duplication

The bootstrap script in the HTML export duplicates rendering logic from `factory.js` / per-entity modules. This is intentional:

- **The HTML file must be self-contained** — no module imports from the Python package.
- **The export is a snapshot** — the renderer code at export time is frozen into the file. If the live renderer changes later, the export remains functional.
- **Maintenance:** when per-entity renderers change, the corresponding functions in `_export.py`'s template must also be updated. A comment in each JS renderer module should note the duplication.

### 5.2 glTF Primitive Generation

The `_gltf.py` module must generate actual vertex/index buffer data for each entity type. This is a significant amount of code — each entity kind needs a primitive generator (sphere vertices, cylinder vertices, torus vertices, etc.). However, the primitives are simple and well-documented:

- Sphere: UV sphere with configurable radius and segments
- Cylinder: Height, radius, segments
- Torus: Major radius, minor radius, segments
- Plane: Width × height quad
- Cone: Height, radius, segments
- Box edges: 12 line segments
- Ring/arc: 2D annulus with angle range

### 5.3 Color Encoding

Both formats use sRGB color space. Tanga colors (hex strings or RGB tuples) are already normalized to hex in `_normalize_color()`. For glTF, we convert hex to linear RGBA floats.

---

## 6. Limitations (Documented)

| Feature | HTML Export | glTF Export |
|---------|-------------|-------------|
| Entity meshes | ✅ | ✅ |
| Operator meshes | ✅ | ✅ |
| Colors and opacity | ✅ | ✅ |
| Style data (Phase 4c) | ✅ | ✅ (partial — geometry params only) |
| Labels | ✅ | ❌ (glTF has no text primitive) |
| Wireframe overlay | ✅ | ✅ (approximated as edges) |
| Grid and axes | ✅ | ❌ (grid/axes are not glTF nodes) |
| Orbit controls | ✅ | ✅ (viewer-dependent) |
| Camera config | ✅ | ✅ (camera node in glTF) |
| Animation | ❌ (static snapshot) | ❌ (static snapshot) |
| Live updates | ❌ | ❌ |

---

## 7. Implementation Checklist

### 7.1 `_export.py` (new) — HTML Export

- [ ] **X1:** Create `py/pytanga/viz/_export.py`
- [ ] **X2:** Implement `_render_export_html(entities, scene_config) -> str`
- [ ] **X3:** Embed scene data as `JSON.stringify()` in a `<script type="application/json">` tag
- [ ] **X4:** Embed scene config (camera, background, grid settings) the same way
- [ ] **X5:** Inline a ~200-line bootstrap JS script that:
  - [ ] Sets up Three.js scene, camera, renderer, orbit controls, CSS2DRenderer
  - [ ] Parses `#tanga-scene-data` and `#tanga-scene-config`
  - [ ] Calls per-entity `create*()` functions (duplicated from Phases 5/6)
  - [ ] Handles labels via CSS2D objects
  - [ ] Applies camera config or auto-fits
  - [ ] Starts render loop
- [ ] **X6:** HTML template includes CDN import map for Three.js 0.170
- [ ] **X7:** Grid helper with configurable size and color
- [ ] **X8:** Axes helper (RGB arrows at origin) if enabled in config

### 7.2 `_gltf.py` (new) — glTF Export

- [ ] **X9:** Create `py/pytanga/viz/_gltf.py`
- [ ] **X10:** Implement glTF binary structure: JSON header + binary buffer
- [ ] **X11:** Implement primitive generators for basic shapes:
  - [ ] Sphere (for Point, HPoint, Sphere, Inversion wireframe)
  - [ ] Cylinder (for Line shaft, arrow shafts)
  - [ ] Cone (for arrow heads, Direction)
  - [ ] Plane/quad (for Plane, Reflection)
  - [ ] Torus (for Circle, Dilator rings)
  - [ ] Box edges (for Space)
  - [ ] Ring/arc (for Rotor disc)
  - [ ] Helix curve (for Motor)
- [ ] **X12:** Implement `_entity_to_gltf_nodes(entity_dict) -> list[dict]` — maps each entity kind to glTF nodes with correct transforms
- [ ] **X13:** Map entity colors to glTF PBR materials (`pbrMetallicRoughness.baseColorFactor`)
- [ ] **X14:** Map opacity to material alpha + `alphaMode: "BLEND"` for translucent entities
- [ ] **X15:** Apply camera node if `CameraConfig` is specified
- [ ] **X16:** Apply entity styles (size, thickness, etc.) to node scales and primitive params

### 7.3 `visualizer.py`

- [ ] **X17:** Add `export_html(path: str | Path) -> None` method
- [ ] **X18:** Add `export_glb(path: str | Path) -> None` method
- [ ] **X19:** Both methods call `self._scene.full_state(defaults=self._defaults)` for the data

### 7.4 Tests

- [ ] **X20:** Test `export_html()` produces valid HTML with `<!DOCTYPE html>` and embedded JSON
- [ ] **X21:** Test exported HTML contains `window.__TANGA_SCENE__` equivalent data
- [ ] **X22:** Test `export_glb()` produces a file starting with glTF magic bytes (`0x46546C67`)
- [ ] **X23:** Test `export_glb()` for each entity kind (9 entities + 8 operators)
- [ ] **X24:** Test exported `.glb` is parseable by a simple glTF validator
- [ ] **X25:** Manual test: open exported `.html` in browser — all entities render, orbit controls work
- [ ] **X26:** Manual test: open exported `.glb` in `<model-viewer>` — scene displays correctly
- [ ] **X27:** Manual test: open exported `.glb` in Blender — meshes appear at correct positions
- [ ] **X28:** Manual test: exported `.html` works when opened from a different directory/machine (CDN)
- [ ] **X29:** All existing tests still pass

### 7.5 Documentation

- [ ] **X30:** Document `export_html()` and `export_glb()` in `docs/py/viz/index.md`
- [ ] **X31:** Add export example to `docs/py/viz/examples.md`
- [ ] **X32:** Add `<model-viewer>` usage instructions for glTF recipients

---

## 8. Verification Checklist

- [ ] `viz.export_html("scene.html")` produces a valid HTML file
- [ ] Exported HTML renders all entity kinds correctly when opened in a browser
- [ ] Orbit controls work (rotate, pan, zoom) in exported HTML
- [ ] Labels are visible and correctly positioned in exported HTML
- [ ] Camera auto-fit works when no explicit `CameraConfig` is set
- [ ] Explicit camera configuration is respected
- [ ] `viz.export_glb("scene.glb")` produces a valid glTF binary file
- [ ] Exported `.glb` opens correctly in `<model-viewer>`
- [ ] Exported `.glb` opens correctly in Blender
- [ ] All 19 entity/operator kinds export to glTF without errors
- [ ] glTF materials use correct colors and opacity
- [ ] Both export methods work without a running server
- [ ] No circular imports introduced
- [ ] All existing tests pass

---

## 9. Relationship to Other Phases

| Phase | Dependency |
|-------|-----------|
| **4c** | Styles must be complete so `style` dicts are available for glTF material mapping |
| **4d** | Labels must be complete so label data is available for HTML export embedding |
| **5/6** | JS renderer code is the template for the inlined bootstrap script in HTML export |
| **8** | Package must be importable and `full_state()` must work end-to-end |
| **10** | Example scripts should include a `demo_export.py` showing both export methods |