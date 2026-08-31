# Interaction & Controls

Interactivity in `pytanga.viz` has three surfaces, from the quickest to the
most custom:

| Surface | API | Where it appears |
|---------|-----|------------------|
| Panel controls | `viz.add_slider` / `add_dropdown` / `add_button` / `add_control_group` / … | A floating panel overlaid on the scene |
| Control views | `SliderView` / `ButtonView` / … inside a `GroupView`/`StackView` | A pane in a split-view layout |
| Object interaction | `InteractionConfig` / `on_interaction` | Directly on scene entities |

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Panel Controls](controls.md) | `add_slider`/`add_dropdown`/`add_button`/`add_control_group` and the other `add_*` controls |
| [Control Views (xxxView)](control-views.md) | The declarative `xxxView` layout/control classes and their mapping to the `add_*` controls |
| [Object Interaction](object-interaction.md) | Click/drag/scroll handlers on scene entities |

!!! note "Control views"
    The declarative `xxxView` layout/control classes (`SliderView`,
    `ButtonView`, `GroupView`, `SplitView`, …) are introduced in
    [Layouts](../app/layouts.md) and documented in full on the
    [Control Views (xxxView)](control-views.md) page.
