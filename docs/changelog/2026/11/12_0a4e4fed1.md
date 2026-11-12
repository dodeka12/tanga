# Changes since version 2.26.1 (2.27.0-rc1)

## Bug Fixes
- **Expanded `GroupView` keeps its flex layout** — `_applyCollapsed()` no longer
  clears the content display set by `_applyFlex()`, so an expanded group renders
  with its `gap` (including `--tanga-stack-gap`) and the size arithmetic matches
  the visible layout again.
- **Runtime-registered theme CSS is revalidated** — files under
  `themes/user/…` are served with `Cache-Control: no-cache`, so editing a custom
  theme and restarting the app no longer leaves an open tab on a stale
  stylesheet.
