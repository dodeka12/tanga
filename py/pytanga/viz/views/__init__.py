# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Declarative view/layout model for the Tanga 3D viewer.

A :class:`View` is a rectangular region with per-axis preferred and min/max
sizes.  Leaves (:class:`SceneView`, :class:`SpacerView`, and the HTML control
views :class:`SliderView`/:class:`ButtonView`/:class:`DropdownView`) and two
containers (:class:`SplitView` with draggable splitters and :class:`StackView`
flow layout) are provided, plus :class:`GroupView` (a titled stack, usable as an
overlay).  The whole tree serializes to the ``view_layout`` message consumed by
the browser frontend.

This package is pure data + validation: it imports nothing from the rendering or
server layers, so it is unit-testable in isolation.
"""

from __future__ import annotations

from ._base import View
from ._enums import EOrientation, EStackAlign, EStackDirection, EStackJustify
from .._size import SizeSpec, size_from_dict
from .camera_view import CameraView
from .control_view import ControlView
from .control_views import (
    ButtonView,
    CheckboxView,
    ColorPickerView,
    DropdownView,
    FileChooserView,
    LabelView,
    MarkdownView,
    ProgressBarView,
    SliderView,
    TableView,
    TextAreaView,
    TextFieldView,
    ValueEditView,
)
from .group_view import GroupView
from .log_view import LogView
from .menu_view import MenuView
from .scene_view import SceneView
from .separator_view import SeparatorView
from .spacer_view import SpacerView
from .split_view import SplitView
from .stack_view import StackView
from .toolbar_view import ToolbarView
from .functions import (
    control_to_view,
    iter_control_views,
    iter_log_views,
    iter_scene_names,
    iter_scene_views,
    serialize_layout,
)

__all__ = [
    "ButtonView",
    "CameraView",
    "CheckboxView",
    "ColorPickerView",
    "ControlView",
    "DropdownView",
    "EOrientation",
    "EStackAlign",
    "EStackDirection",
    "EStackJustify",
    "FileChooserView",
    "GroupView",
    "LabelView",
    "LogView",
    "MarkdownView",
    "MenuView",
    "ProgressBarView",
    "SceneView",
    "SeparatorView",
    "SizeSpec",
    "SliderView",
    "SpacerView",
    "SplitView",
    "StackView",
    "TableView",
    "TextAreaView",
    "TextFieldView",
    "ToolbarView",
    "ValueEditView",
    "View",
    "control_to_view",
    "iter_control_views",
    "iter_log_views",
    "iter_scene_names",
    "iter_scene_views",
    "serialize_layout",
    "size_from_dict",
]
