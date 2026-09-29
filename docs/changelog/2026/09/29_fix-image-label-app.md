# Changes since version 2.12.1

## New Features

- **Screen-space point markers** — `SquarePointStyle` / `CirclePointStyle` /
  `IconPointStyle` / `CrossHairPointStyle` gain a `screen_space` flag; when set,
  `size` (and `thickness` / `arm_thickness`) are interpreted as CSS pixels and
  the marker is rescaled every frame to a constant on-screen size (uniform in
  ortho, distance-based + billboarded in perspective).  Act composite handles
  opt in by default.
- **Image minification** — `ImageCanvas` gains `min_zoom` (default `0.25`), so an
  image can be zoomed out to 1/4 of its fit size instead of being locked at 1:1.

## Bug Fixes

- **Late image pixel frame** — an image whose binary pixel frame arrives after
  its entity JSON no longer renders black; the renderer re-attaches the texture
  when the frame lands.
