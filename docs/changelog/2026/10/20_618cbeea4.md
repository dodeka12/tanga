# Changes since version 2.21.1

## Bug Fixes
- **Depth images render in every pane** — the depth-image renderer now peeks its
  depth/image/segmentation frames instead of consuming them, so two `SceneView`s
  of one scene share the same pixels instead of the second view falling back to a
  flat white surface; frames are released when the entity or scene is removed.
- **Pinhole depth surfaces no longer mirror vertically** — the pinhole vertex and
  radial-depth math now invert the texture `v` coordinate so the surface lines up
  with the image it was measured from; `pinhole_depth.py` demonstrates the fix
  with a two-pane image/3D view and a sine-pattern-driven depth map.
