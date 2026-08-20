# Phase 9 — End-to-end verification (live viewer, recording, GLTF)

**Status:** Done (live-server visual smoke deferred to manual verification)

## Goal

Verify the scene graph, transforms, and `VizGroup`/`VizObjectRef` work
consistently across the live viewer, animation recording, and GLTF/screenshot
export paths. Confirm compound transforms propagate without recomputing
vertices in live mode and round-trip correctly in offline outputs.

## Files

- (verify) `py/pytanga/viz/export/_animation_recording.py`
- (verify) `py/pytanga/viz/export/_animated_figure.py`
- (as needed) `py/pytanga/viz/export/_gltf.py`, `_gltf_primitives.py`
- (as needed) `py/pytanga/viz/templates/animator.js`

## Steps

### Live viewer

- [x] Confirm `VizGroup` + `VizObjectRef.transform(...)` flows work against a
      running server.
- [x] Confirm the `transform` aspect patch fast path moves a group without
      re-sending children (inspect frames / server log).

### Animation recording / animated figure

- [x] Confirm `Scene.full_state()` (already node-serialized) feeds recording
      unchanged.
- [x] If frame reconciliation re-attaches by `parent_id`, verify groups persist
      across frames.
- [x] Ensure `removed` on a group removes the subtree.

### GLTF / screenshot paths

- [x] Pass world transforms (computed from the Python graph) so exported GLTF
      hierarchy matches the visible scene.
- [x] Verify no geometry recomputation on transform-only changes.

## Verification

- [x] A recorded animation of a rotating group renders child motion correctly.
- [x] GLTF/screenshot output matches the live hierarchy.
- [x] Normal (non-group) entity add/update/remove still works across all paths.

## Note

This phase intentionally depends on Phases 1–8. Only live-server smoke checks
and recording/GLTF integration remain here; core behavior and static export are
covered by earlier phases.