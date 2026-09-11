# Bug: `show(layout=…)` does not open the layout URL (default reconnect path)

**Created:** 2026-08-31 | **Status:** Reported | **Branch:** `seating-plan-app`

A standalone bug description for the pytanga repo. It documents why
`Visualizer.show(layout=…)` shows a blank/single scene instead of the split-view
layout when the default `reuse_existing=True, wait_for_browser=True` options are
used.

## Metadata

- Package: `tanga-py` (import name `pytanga`), version **1.11.0**.
- Module: `pytanga/viz/visualizer.py` (browser opening) · `pytanga/viz/server.py`
  (WS ready handling) · `pytanga/viz/templates/viewer.js` (frontend URL parsing).
- Severity: high — the documented `show(layout=…)` usage silently renders the
  wrong thing (main scene, no layout) with no error.

## Summary

`show(layout=…)` computes the layout URL `/?view=<name>&token=<t>` but, in the
default `reuse_existing=True, wait_for_browser=True` path, never opens that URL.
Instead `wait_for_browser()` opens `/?token=<t>` (no `?view=`), so the frontend
never sees `view` and falls back to single-scene mode. The result is an empty
main scene and `controls_define controls=0` in the browser console — no split
view, no layout controls.

## Steps to reproduce

```python
from pytanga.viz import ButtonView, GroupView, SceneView, SplitView, Visualizer

layout = SplitView(
    "horizontal",
    [GroupView("Controls", [ButtonView("btn", label="Go")]), SceneView("")],
)

viz = Visualizer()              # reuse_existing=True by default
viz.show(layout=layout)         # wait_for_browser=True by default
viz.wait()
```

1. Run the script.
2. Press **Enter** at the "Press Enter to open a new browser tab…" prompt
   (or let an existing tab reconnect).
3. Observe the page.

### Expected

The browser opens `/?view=&token=…`; the frontend sends `type=ready layout=''`;
the server responds with a `view_layout` message; the split view renders.

### Actual

The browser opens `/?token=…` (no `?view=`); the frontend sends
`type=ready scene=`; the server serves only the main scene. Console shows:

```
[tanga:ws-send] type=ready scene= token=…          # no `layout=`
[tanga:init]    controls_define controls=0 groups=0
[tanga:init]    scene_list scenes=[""]
[tanga:init]    scene_update objects=2 removed=0    # just default axes/grid
```

## Root cause

1. `_open_layout_browser` (`visualizer.py:1543`) builds the correct URL:

   ```python
   token_url = f"/?view={layout_name}&token={page_token}"
   return self._open_browser_url(token_url, wait_for_browser=wait_for_browser)
   ```

2. `_open_browser_url` (`visualizer.py:1556`) only uses `token_url` in the
   `reuse_existing=False` branch and the `wait_for_browser=False` branch. In the
   default branch it calls `wait_for_browser()` and **discards** `token_url`:

   ```python
   if self._reuse_existing:
       if wait_for_browser:
           connected = self.wait_for_browser(timeout=120.0)   # token_url unused
           if not connected:
               return False
       else:
           …  # only this branch opens token_url
   else:
       …  # reuse_existing=False branch opens token_url
   ```

3. `wait_for_browser` (`visualizer.py:1724`), when the user presses Enter,
   opens a URL **without** `?view=` (`visualizer.py:1788`):

   ```python
   self._server.open_browser(f"/?token={page_token}")
   ```

4. The frontend only enters layout mode when the `view` query param is present
   (`viewer.js:52-55`):

   ```js
   let _layoutName = (() => {
       const params = new URLSearchParams(window.location.search);
       return params.has('view') ? (params.get('view') || '') : null;
   })();
   ```

   With no `view` param, `_layoutName` is `null`, so the `ready` message omits
   `layout` (`viewer.js:212-215`) and the server takes the single-scene branch
   (`server.py:683`, `server.py:723`).

Note: the frontend already treats a *present-but-empty* `view` (`?view=`) as
layout mode, so the only defect is that the opened URL never includes `?view=`.

## Suggested fix

Make the default reconnect/Enter path open the pending layout URL rather than the
plain one. Two options:

- **Pass the URL through** — give `wait_for_browser` an optional `path` argument
  and open it instead of the hard-coded `/?token=…`:

  ```python
  # in _open_browser_url
  if wait_for_browser:
      connected = self.wait_for_browser(timeout=120.0, path=token_url)
  ```

  ```python
  def wait_for_browser(self, timeout: float = 120.0, path: str | None = None) -> bool:
      …
      self._server.open_browser(path or f"/?token={page_token}")
  ```

- **Open before waiting** — in the `reuse_existing=True` branch, call
  `self._server.open_browser(token_url)` before `wait_for_browser(...)`, so the
  layout URL is what actually opens/reconnects (mirroring the
  `reuse_existing=False` branch).

Also consider printing the layout URL (not just `self.url`) in the connect
prompt so manual copy/paste keeps the `?view=` param.

## Workaround (used downstream)

Set `reuse_existing=False` (as `py/examples/viz/scenes/split_view.py` already
does), which takes the branch that opens `token_url` directly. In the
`seating-plan-app` repo this is applied in `src/seating_plan/app.py`.
