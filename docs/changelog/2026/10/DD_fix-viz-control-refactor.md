# Changes since version 2.15.0

## Refactor
- **Explicit typed `ControlView` forwarders** — `ControlView.__getattr__`
  (which returned `Any`) is removed in favour of explicit typed `@property`
  reads and setters/methods on the base and each concrete control view, so the
  control-view API is introspectable and type-checked; `menu_view` now uses a
  runtime-checkable `VariantControl` `Protocol` instead of `getattr`/`hasattr`
  duck-typing.
- **Runtime-checkable structural `Protocol`s for the viz tree** —
  `toolbar_view`, `functions.py`, and `_layout.py` replace `getattr`/`hasattr`
  duck-typing (the `variant`, `scene`/`children`/`overlay`, `position`, `id`,
  and control handler / file-chooser field checks) with `@runtime_checkable`
  `Protocol`s (`VariantControl`, `HasOnChange`, `HasChildren`, `HasOverlay`,
  `HasScene`, `Positionable`) and `isinstance` narrowing, so the view/control
  tree is typed and introspectable with no behavior change.
