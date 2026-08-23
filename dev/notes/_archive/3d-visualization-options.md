# 3D Visualization Library Options for Tanga Geometic Entities

**Requirement:** Display 3D geometric entities (Points, Lines, Planes, Spheres, Circles, Directions, PointPairs, etc.) in an interactive window with rotation, pan, zoom, and translucent rendering. Must work in a web browser with WebGL.

---

## Top Recommendations

### 1. ⭐ Three.js (Direct JavaScript/TypeScript)

**Approach:** Write a thin HTML/JS frontend that loads entity data from Python (JSON export) and renders via Three.js.

| Aspect | Assessment |
|--------|-----------|
| **WebGL-native** | ✅ Gold standard for WebGL. Battle-tested across all browsers. |
| **Interaction** | ✅ OrbitControls gives perfect rotate/pan/zoom out of the box. |
| **Translucency** | ✅ Materials support `opacity` + `transparent: true`. Wireframe + translucent fill possible simultaneously. |
| **Primitives** | ✅ Built-in: `SphereGeometry`, `CylinderGeometry` (lines as thin cylinders), `PlaneGeometry`, `CircleGeometry`, `PointsMaterial` for point clouds. Even has `LineSegments` for wireframe edges. |
| **Custom geometry** | ✅ `BufferGeometry` for arbitrary triangle meshes. Can render planes as semi-transparent quads, lines as cylinders or line strips. |
| **Ecosystem** | ✅ Enormous — react-three-fiber for React, tons of examples, OrbitControls, TransformControls, etc. |
| **Python bridge** | ✅ Export entities as JSON from Python; trivial to consume in JS. Could also use a lightweight HTTP/WebSocket server. |
| **Staying power** | ✅ Most popular 3D library on GitHub (~100k stars). MIT license. |

**How it maps to Tanga entities:**
| Entity | Three.js representation |
|--------|------------------------|
| `Point` | `SphereGeometry` (small sphere) or `PointsMaterial` (dot) |
| `Direction` | Arrow (cone + cylinder) or line from origin to direction |
| `Line` | `CylinderGeometry` (thin tube) extended to infinity → bounded segment with fade |
| `Plane` | `PlaneGeometry` with translucent material, large quad |
| `Circle` | `RingGeometry` or `TorusGeometry` (thin) |
| `Sphere` | `SphereGeometry` with wireframe + translucent fill |
| `PointPair` | Two points connected by a thin line |
| `Space` | Bounding box outline or large translucent cube |
| `Rotor`/`Motor` | Curved arrow or arc showing rotation, arrow for translation |

**Verdict:** Best option for maximum flexibility, quality, and web-native performance. More implementation effort initially (manual JSON serialization + JS frontend) but pays off long-term.

---

### 2. ⭐ PyVista (Python with Web Export)

**Approach:** Build viz in Python using PyVista's high-level API; export to HTML/WebGL via `pythreejs` backend or `.export_html()`.

| Aspect | Assessment |
|--------|-----------|
| **WebGL** | ✅ Via `pythreejs` (Jupyter) or `panel` + `vtk.js`. Can export standalone HTML files. |
| **Interaction** | ✅ Built-in rotate/pan/zoom in both desktop window and Jupyter. |
| **Translucency** | ✅ `opacity` parameter on all actors. |
| **Primitives** | ✅ `pv.Sphere()`, `pv.Arrow()`, `pv.Plane()`, `pv.Line()`, `pv.Circle()`, `pv.Cylinder()`, `pv.Cube()`. Everything needed. |
| **Python-native** | ✅ No JavaScript code required. All entity construction in Python. |
| **Integration** | ✅ Can directly consume `pytanga.geometry` entity objects; write a simple converter function. |
| **Stability** | ✅ Mature project, VTK-backed, widely used in scientific computing. |

**Verdict:** Best option if you want to stay in Python and avoid writing JavaScript. More limited customization than raw Three.js but much faster to prototype. The `.export_html()` feature directly meets the web browser requirement.

---

### 3. Vedo (Python, VTK-based, Modern API)

**Approach:** Similar to PyVista but with an arguably more elegant API for geometric entities.

| Aspect | Assessment |
|--------|-----------|
| **WebGL** | ✅ Export to HTML via `vedo.export_html()` or k3d backend. Also has `vedo.serve_web()` for interactive remote viewing. |
| **Interaction** | ✅ Excellent interactivity out of the box. |
| **Translucency** | ✅ `alpha` parameter on all objects. |
| **Geometric focus** | ✅ Strongly aligned — has `Point`, `Line`, `Plane`, `Sphere`, `Circle`, `Arrow` as first-class objects. |
| **Documentation** | ✅ Very good examples, specifically for scientific/geometric visualization. |

**Verdict:** Very close to PyVista. Vedo's API may feel more natural for geometric algebra entities since their primitives map almost 1:1. Slightly smaller community but excellent for this specific use case.

---

### 4. Plotly (Python, WebGL via plotly.graph_objects)

**Approach:** Use Plotly's 3D scatter and mesh traces.

| Aspect | Assessment |
|--------|-----------|
| **WebGL** | ✅ Uses WebGL for 3D rendering in the browser. |
| **Interaction** | ✅ Built-in rotate/pan/zoom in the browser. |
| **Translucency** | ✅ `opacity` on markers and surfaces. |
| **Primitives** | ⚠️ Limited — good for points (`Scatter3d`), meshes (`Mesh3d`), and surfaces (`Surface`). No native sphere/cylinder/arrow. Must construct meshes manually. |
| **Python-native** | ✅ Pure Python, HTML export via `write_html()`. |

**Verdict:** Great for point clouds and surfaces, but awkward for lines, planes, spheres, and circles. Not recommended for this use case given the entity types involved.

---

## Summary Comparison

| Library | WebGL | Python-native | Primitives match | Translucency | Effort |
|---------|-------|---------------|-----------------|--------------|--------|
| **Three.js** | ✅✅✅ | ❌ (JS) | ✅ (manual) | ✅ | Medium-High |
| **PyVista** | ✅✅ | ✅ | ✅✅ | ✅ | Low-Medium |
| **Vedo** | ✅✅ | ✅ | ✅✅✅ | ✅ | Low |
| **Plotly** | ✅ | ✅ | ⚠️ | ✅ | Medium |

---

## Recommendation

**For fastest path to a working prototype:** Use **Vedo**. Its primitives align almost perfectly with Tanga's entity types, it requires zero JavaScript, and it can export standalone HTML files for browser viewing.

**For the most polished, flexible, production-quality result:** Use **Three.js** with a Python→JSON export layer. This gives full control over rendering style, handles edge cases (infinite planes/lines), and produces the best web experience. The upfront cost is higher but it's a one-time investment.

**Suggested hybrid approach:** Start with Vedo for rapid prototyping and debugging, then graduate to a custom Three.js frontend once the visualization requirements solidify.