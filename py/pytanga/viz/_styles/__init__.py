# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Visualization style dataclasses for the Tanga 3D viewer.

Each entity/operator kind has a dedicated style class that defines
its visual appearance (size, thickness, extent, color, opacity, etc.).
Styles are serialized to JSON via ``to_dict()`` so the frontend can
dispatch on ``style_type``.

All fields default to ``None``.  The ``Visualizer`` stores fully-initialized
canonical instances in ``_DEFAULT_STYLE_FOR_KIND``; when a user supplies a
sparse style (only some fields set), the serializer merges the user's non-``None``
values with the canonical default.
"""

from __future__ import annotations

from typing import Any, TypeAlias, Union

from pytanga.geometry.entities import (
    Arc,
    Circle,
    Cylinder,
    Direction,
    HPoint,
    ImagCircle,
    ImagPointPair,
    ImagSphere,
    Line,
    Plane,
    Point,
    PointPair,
    Space,
    Sphere,
)
from pytanga.geometry.operators import (
    Dilator,
    GeneralRotor,
    Inversion,
    Motor,
    ReflectionLine,
    ReflectionPlane,
    ReflectionPoint,
    Rotor,
    Translator,
)

from ._base import (
    DashedWireframe,
    DottedWireframe,
    SolidWireframe,
    VizStyle,
    WireframeDashPattern,
)
from ._entity_styles import (
    ArcStyle,
    Axes2DStyle,
    Axes3DStyle,
    AxisStyle,
    CircleStyle,
    CylinderLineStyle,
    CylinderStyle,
    DirectionStyle,
    GridStyle,
    HPointStyle,
    LineStyle,
    PlaneStyle,
    PointPairStyle,
    PointPathStyle,
    PointStyle,
    SpaceStyle,
    SphereStyle,
)
from ._operator_styles import (
    CrossHairPointStyle,
    DilatorStyle,
    GeneralRotorStyle,
    InversionStyle,
    MotorStyle,
    ReflectionLineStyle,
    ReflectionPlaneStyle,
    ReflectionPointStyle,
    RotorStyle,
    TranslatorStyle,
)
from ._sdf_style import SdfStyle
from ._overlay_styles import (
    AnimStyle,
    AnnotationStyle,
    FigureStyle,
    LabelStyle,
    TitleStyle,
)
from ._tex_label_style import TextureLabelStyle

# ── Union type ──────────────────────────────────────────────

ObjVizStyle: TypeAlias = Union[
    PointStyle,
    DirectionStyle,
    HPointStyle,
    PointPairStyle,
    LineStyle,
    PlaneStyle,
    CircleStyle,
    CylinderLineStyle,
    CylinderStyle,
    ArcStyle,
    SphereStyle,
    SpaceStyle,
    ReflectionLineStyle,
    ReflectionPlaneStyle,
    ReflectionPointStyle,
    InversionStyle,
    RotorStyle,
    TranslatorStyle,
    DilatorStyle,
    MotorStyle,
    GeneralRotorStyle,
    CrossHairPointStyle,
    PointPathStyle,
    GridStyle,
    AxisStyle,
    Axes2DStyle,
    Axes3DStyle,
    SdfStyle,
]


# ── Canonical defaults (fully-initialized) ──────────────────

_DEFAULT_STYLE_FOR_KIND: dict[str, VizStyle] = {
    "Point": PointStyle(color="#ff4444", opacity=1.0, size=0.08),
    "Direction": DirectionStyle(color="#ffffff", opacity=0.9, length=2.0),
    "HPoint": HPointStyle(color="#ff8844", opacity=1.0, size=0.08),
    "PointPair": PointPairStyle(
        color="#44ff44", opacity=1.0, point_size=0.06, line_thickness=1.0
    ),
    "Line": LineStyle(color="#44ff44", opacity=0.8, length=20.0, thickness=1.0),
    "Plane": PlaneStyle(color="#4488ff", opacity=0.3, extent=10.0),
    "Circle": CircleStyle(color="#ff44ff", opacity=1.0, tube_radius=0.03),
    "Sphere": SphereStyle(color="#ffaa00", opacity=0.4, wireframe=True),
    "Cylinder": CylinderStyle(color="#44aaff", opacity=0.9),
    "Arc": ArcStyle(color="#ffcc44", opacity=0.9),
    "Space": SpaceStyle(color="#888888", opacity=0.1, extent=10.0),
    "PointPath": PointPathStyle(color="#ffffff", opacity=1.0, line_thickness=2.0),
    "Grid": GridStyle(color="#555555", opacity=0.8, line_thickness=1.0),
    "Axis": AxisStyle(
        color="#888888",
        opacity=1.0,
        line_thickness=2.0,
        label_style=LabelStyle(along=0.5, align=(0.5, 0.0), offset_2d=(0.0, 10.0)),
        value_style=LabelStyle(font_size=12, align=(0.5, 0.5)),
    ),
    "Axes2D": Axes2DStyle(),
    "Axes3D": Axes3DStyle(),
    # Operators
    "ReflectionLine": ReflectionLineStyle(
        color="#aaccff", opacity=0.6, length=5.0, thickness=0.04
    ),
    "ReflectionPlane": ReflectionPlaneStyle(color="#88ccff", opacity=0.35, extent=5.0),
    "ReflectionPoint": ReflectionPointStyle(color="#ffffff", opacity=0.5, extent=1.0),
    "Inversion": InversionStyle(color="#cc88ff", opacity=0.4),
    "Rotor": RotorStyle(color="#ff8844", opacity=0.7, disc_radius=1.5),
    "Translator": TranslatorStyle(color="#44aaff", opacity=0.9, length=3.0),
    "Dilator": DilatorStyle(color="#ffcc44", opacity=0.6, ring_count=4, max_radius=3.0),
    "Motor": MotorStyle(color="#ff66cc", opacity=0.7),
    "GeneralRotor": GeneralRotorStyle(color="#ff9966", opacity=0.6),
    # Imaginary entity variants
    "ImagPointPair": PointPairStyle(
        color="#ff88ff",
        opacity=1.0,
        point_size=0.06,
        line_thickness=1.0,
        wireframe=True,
        wireframe_dash=DottedWireframe(),
        wireframe_opacity=0.6,
    ),
    "ImagCircle": CircleStyle(
        color="#ff88ff",
        opacity=0.0,
        tube_radius=0.03,
        wireframe=True,
        wireframe_dash=DottedWireframe(),
        wireframe_opacity=0.6,
    ),
    "ImagSphere": SphereStyle(
        color="#ff8844",
        opacity=0.3,
        wireframe=True,
        wireframe_dash=DottedWireframe(),
        wireframe_opacity=0.6,
    ),
}


# ── Helper functions ────────────────────────────────────────


def _default_style_for(
    entity: (
        Point
        | Direction
        | HPoint
        | PointPair
        | ImagPointPair
        | Line
        | Plane
        | Circle
        | ImagCircle
        | Sphere
        | ImagSphere
        | Space
        | Cylinder
        | Arc
        | ReflectionLine
        | ReflectionPlane
        | ReflectionPoint
        | Inversion
        | Rotor
        | Translator
        | Dilator
        | Motor
        | GeneralRotor
    ),
) -> VizStyle:
    """Return the default style instance for a given entity/operator type."""
    kind = type(entity).__name__
    return _DEFAULT_STYLE_FOR_KIND[kind]


def _style_for_kind(
    kind: str,
    styles_map: dict[str, VizStyle] | None = None,
) -> VizStyle:
    """Return the default style for a kind string (e.g. ``"Point"``)."""
    source = styles_map if styles_map is not None else _DEFAULT_STYLE_FOR_KIND
    return source.get(kind, VizStyle())


def _style_to_output(
    style: VizStyle | dict[str, Any] | None,
    kind: str,
    styles_map: dict[str, VizStyle] | None = None,
) -> dict[str, Any]:
    """Resolve a (possibly partial) style to a complete merged dict.

    The merge happens **Python-side** — the JS renderers always receive a
    complete style dict.
    """
    canonical = _style_for_kind(kind, styles_map=styles_map)

    if style is None:
        return canonical.to_dict() if hasattr(canonical, "to_dict") else {}

    if isinstance(style, VizStyle):
        user_dict = style.to_dict()
        canonical_dict = canonical.to_dict() if hasattr(canonical, "to_dict") else {}
        merged = dict(canonical_dict)
        for k, v in user_dict.items():
            if v is not None:
                merged[k] = v
        return merged

    if isinstance(style, dict):
        return style

    return {}
