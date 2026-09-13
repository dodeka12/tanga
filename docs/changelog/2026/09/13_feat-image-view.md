# Changes since version 2.3.0 (2.4.0-rc3)

## New Features
- **Image display via `ImageCanvas`** — display numpy (`uint8`/`uint16`/`float32`,
  1/3/4-channel) and PIL images on a shader-drawn plane with a pixel-coordinate
  frame (y-down, 1 unit = 1 pixel), per-image shaders/uniforms, mouse-driven
  uniform updates, and raw binary image transfer over the existing WebSocket.
