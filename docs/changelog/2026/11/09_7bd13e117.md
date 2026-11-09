# Changes since version 2.25.1

## Bug Fixes
- **CD: macOS wheels build on `macos-15` again** — GitHub retired all macOS 14
  runner images on 2026-11-02, so both macOS legs of the release workflow were
  cancelled (`The configuration 'macos-14-arm64-us-default' is not supported`)
  and the publish, tag and docs-deploy jobs were skipped.
- **macOS wheel tag follows `MACOSX_DEPLOYMENT_TARGET`** — `fix-wheel-tag.py`
  now takes `macosx_<major>_<minor>_<arch>` from the pinned deployment target
  (CI uses `14.0`) instead of the build host's macOS version, so building on a
  newer runner keeps the wheel installable on macOS 14+.
- **Debug build workflow uses supported macOS runners** — the retired
  `macos-13` / `macos-14` choices are replaced by `macos-15`, `macos-15-intel`
  and `macos-26`, with the same pinned deployment target as the release
  workflow.
- **Installation docs list macOS wheels** — `README.md` and the installation
  guide now state that precompiled wheels exist for Linux (x86_64), Windows
  (win_amd64) and macOS 14+ (arm64), and that other platforms fall back to the
  pure wheel plus the `compile` extra.
