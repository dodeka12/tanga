# Interaction & Controls

Interactivity in `pytanga.viz` has two surfaces, from the quickest to the
most custom:

| Surface | API | Where it appears |
|---------|-----|------------------|
| Controls | `SliderView` / `ButtonView` / `DropdownView` / `GroupView` / … | A pane in a layout, or a `GroupView`/`MenuView` overlay on a scene |
| Object interaction | `InteractionConfig` / `on_interaction` | Directly on scene entities |

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Controls](controls.md) | The control kinds (`SliderView`, `DropdownView`, `ButtonView`, `TableView`, …) and their handler payloads |
| [Control Views (xxxView)](control-views.md) | The declarative `xxxView` layout/control classes and their constructor signatures |
| [Object Interaction](object-interaction.md) | Click/drag/scroll handlers on scene entities |

!!! note "Control views"
    The declarative `xxxView` layout/control classes (`SliderView`,
    `ButtonView`, `GroupView`, `SplitView`, …) are introduced in
    [Layouts](../app/layouts.md) and documented in full on the
    [Control Views (xxxView)](control-views.md) page.
