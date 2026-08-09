# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Interactive 3D visualization of geometric entities via Three.js.

Provides a zero-dependency (on the browser side) WebSocket + Three.js
pipeline for visualizing pytanga.geometry entities in a web browser.

Usage::

    from pytanga.viz import Visualizer, CameraConfig
    from pytanga.geometry import Point

    viz = Visualizer()
    viz.add(Point(1, 2, 3), color="#ff4444")
    viz.run()  # opens browser, blocks until Ctrl+C

    # Explicit camera settings
    viz = Visualizer(
        camera=CameraConfig(position=(10, 6, 12), target=(0, 0, 0), fov=50),
        space_extent=15,
    )
    viz.run()
"""

from ._app import VisualizerApp
from ._controls import Button, ControlGroup, Dropdown, Slider
from ._figure import FigureConfig
from ._label import Label
from ._scene_handle import VizSceneHandle
from ._styles import (
    AnimStyle,
    AnnotationStyle,
    CircleStyle,
    CrossHairPointStyle,
    DilatorStyle,
    DirectionStyle,
    FigureStyle,
    GeneralRotorStyle,
    HPointStyle,
    InversionStyle,
    LabelStyle,
    LineStyle,
    MotorStyle,
    ObjVizStyle,
    PlaneStyle,
    PointPairStyle,
    PointStyle,
    ReflectionLineStyle,
    ReflectionPlaneStyle,
    RotorStyle,
    SpaceStyle,
    SphereStyle,
    TitleStyle,
    TranslatorStyle,
    VizStyle,
)
from ._types import VizInputType
from .export._exporter import SceneExporter
from .scene import CameraConfig, SceneConfig
from .visualizer import Timeline, Visualizer

__all__ = [
    "AnimStyle",
    "AnnotationStyle",
    "Button",
    "CameraConfig",
    "CircleStyle",
    "ControlGroup",
    "CrossHairPointStyle",
    "DilatorStyle",
    "DirectionStyle",
    "Dropdown",
    "FigureConfig",
    "FigureStyle",
    "GeneralRotorStyle",
    "HPointStyle",
    "InversionStyle",
    "Label",
    "LabelStyle",
    "LineStyle",
    "MotorStyle",
    "ObjVizStyle",
    "PlaneStyle",
    "PointPairStyle",
    "PointStyle",
    "ReflectionLineStyle",
    "ReflectionPlaneStyle",
    "RotorStyle",
    "SceneConfig",
    "SceneExporter",
    "Slider",
    "SpaceStyle",
    "SphereStyle",
    "Timeline",
    "TitleStyle",
    "TranslatorStyle",
    "Visualizer",
    "VisualizerApp",
    "VizSceneHandle",
    "VizInputType",
    "VizStyle",
]
