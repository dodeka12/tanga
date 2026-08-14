# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Interactive 3D visualization of geometric entities via Three.js.

Provides a zero-dependency (on the browser side) WebSocket + Three.js
pipeline for visualizing pytanga.geometry entities in a web browser.

Usage::

    from pytanga.viz import Visualizer, CameraConfig3d
    from pytanga.geometry import Point

    viz = Visualizer()
    viz.add(Point(1, 2, 3), color="#ff4444")
    viz.run()  # opens browser, blocks until Ctrl+C

    # Explicit camera settings
    viz = Visualizer(
        camera=CameraConfig3d(position=(10, 6, 12), target=(0, 0, 0), fov=50),
    )
    viz.run()
"""

from ._active import ActHandler, ActPoint, ActSceneObject
from ._act_style import ActObjectStyle, ActPointStyle
from ._app import VisualizerApp
from ._controls import Button, ControlEvent, ControlGroup, Dropdown, Slider
from ._figure import FigureConfig
from ._interaction import (
    Camera,
    ClickEvent,
    DragEvent,
    DragMode,
    Handler,
    InteractionConfig,
    InteractionEventType,
    InteractionHandlerRegistry,
    InteractionTrigger,
    ModifierKey,
    MouseButton,
    ScrollEvent,
)
from ._label import Label
from ._point_path import PointPath, gradient_colors, multi_gradient_colors
from ._scene_handle import VizSceneHandle
from ._scene_objects import Axes2D, Axes3D, Axis, Grid
from ._styles import (
    AnimStyle,
    AnnotationStyle,
    Axes2DStyle,
    Axes3DStyle,
    AxisStyle,
    CircleStyle,
    CrossHairPointStyle,
    DilatorStyle,
    DirectionStyle,
    FigureStyle,
    GeneralRotorStyle,
    GridStyle,
    HPointStyle,
    InversionStyle,
    LabelStyle,
    LineStyle,
    MotorStyle,
    ObjVizStyle,
    PlaneStyle,
    PointPairStyle,
    PointPathStyle,
    PointStyle,
    ReflectionLineStyle,
    ReflectionPlaneStyle,
    RotorStyle,
    SpaceStyle,
    SphereStyle,
    TextureLabelStyle,
    TitleStyle,
    TranslatorStyle,
    VizStyle,
)
from ._types import SceneEntity, VizInputType
from .camera import (
    CameraConfig,
    CameraConfig2d,
    CameraConfig3d,
    View2DConfig,
    View3dConfig,
    get_camera,
    get_camera_view2d,
    get_camera_view3d,
)
from .export._exporter import SceneExporter
from .scene import SceneConfig
from .visualizer import Timeline, Visualizer

__all__ = [
    "ActHandler",
    "ActObjectStyle",
    "ActPoint",
    "ActPointStyle",
    "ActSceneObject",
    "AnimStyle",
    "AnnotationStyle",
    "Axes2D",
    "Axes2DStyle",
    "Axes3D",
    "Axes3DStyle",
    "Axis",
    "AxisStyle",
    "Button",
    "Camera",
    "CameraConfig",
    "CameraConfig2d",
    "CameraConfig3d",
    "ClickEvent",
    "ControlEvent",
    "CircleStyle",
    "ControlGroup",
    "CrossHairPointStyle",
    "DilatorStyle",
    "DirectionStyle",
    "DragEvent",
    "DragMode",
    "Dropdown",
    "FigureConfig",
    "FigureStyle",
    "GeneralRotorStyle",
    "Grid",
    "GridStyle",
    "get_camera",
    "get_camera_view2d",
    "get_camera_view3d",
    "Handler",
    "HPointStyle",
    "InteractionConfig",
    "InteractionEventType",
    "InteractionHandlerRegistry",
    "InteractionTrigger",
    "InversionStyle",
    "Label",
    "LabelStyle",
    "LineStyle",
    "ModifierKey",
    "MouseButton",
    "MotorStyle",
    "ObjVizStyle",
    "PlaneStyle",
    "PointPath",
    "PointPathStyle",
    "PointPairStyle",
    "PointStyle",
    "ReflectionLineStyle",
    "ReflectionPlaneStyle",
    "RotorStyle",
    "SceneConfig",
    "SceneEntity",
    "SceneExporter",
    "ScrollEvent",
    "Slider",
    "SpaceStyle",
    "SphereStyle",
    "TextureLabelStyle",
    "Timeline",
    "gradient_colors",
    "multi_gradient_colors",
    "TitleStyle",
    "TranslatorStyle",
    "View2DConfig",
    "View3dConfig",
    "Visualizer",
    "VisualizerApp",
    "VizSceneHandle",
    "VizInputType",
    "VizStyle",
]
