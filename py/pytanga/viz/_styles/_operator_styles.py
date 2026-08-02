# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Visualization style dataclasses for geometric operators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._base import VizStyle
from ._entity_styles import PointStyle


@dataclass
class ReflectionLineStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.ReflectionLine`."""

    color: str | None = None
    opacity: float | None = None
    length: float | None = None
    thickness: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "ReflectionLineStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.length is not None:
            result["length"] = self.length
        if self.thickness is not None:
            result["thickness"] = self.thickness
        return result


@dataclass
class ReflectionPlaneStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.ReflectionPlane`."""

    color: str | None = None
    opacity: float | None = None
    extent: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "ReflectionPlaneStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.extent is not None:
            result["extent"] = self.extent
        return result


@dataclass
class ReflectionOriginStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.ReflectionOrigin`."""

    color: str | None = None
    opacity: float | None = None
    extent: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "ReflectionOriginStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.extent is not None:
            result["extent"] = self.extent
        return result


@dataclass
class InversionStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.Inversion`.

    No size parameters — radius comes from the entity itself.
    """

    color: str | None = None
    opacity: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "InversionStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        return result


@dataclass
class RotorStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.Rotor`."""

    color: str | None = None
    opacity: float | None = None
    disc_radius: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "RotorStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.disc_radius is not None:
            result["disc_radius"] = self.disc_radius
        return result


@dataclass
class TranslatorStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.Translator`."""

    color: str | None = None
    opacity: float | None = None
    length: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "TranslatorStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.length is not None:
            result["length"] = self.length
        return result


@dataclass
class DilatorStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.Dilator`."""

    color: str | None = None
    opacity: float | None = None
    ring_count: int | None = None
    max_radius: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "DilatorStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.ring_count is not None:
            result["ring_count"] = self.ring_count
        if self.max_radius is not None:
            result["max_radius"] = self.max_radius
        return result


@dataclass
class MotorStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.Motor`.

    No dedicated parameters — uses sub-entity defaults.
    """

    color: str | None = None
    opacity: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "MotorStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        return result


@dataclass
class GeneralRotorStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.GeneralRotor`.

    No dedicated parameters — uses sub-entity defaults.
    """

    color: str | None = None
    opacity: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "GeneralRotorStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        return result


@dataclass
class GeneralDilatorStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.GeneralDilator`."""

    color: str | None = None
    opacity: float | None = None
    ring_count: int | None = None
    max_radius: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "GeneralDilatorStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.ring_count is not None:
            result["ring_count"] = self.ring_count
        if self.max_radius is not None:
            result["max_radius"] = self.max_radius
        return result


@dataclass
class CrossHairPointStyle(PointStyle):
    """Extended point style — renders a 3D crosshair instead of a sphere.

    Inherits ``color``, ``opacity``, and ``size`` from ``PointStyle``.
    ``size`` controls the overall scale (length of each crosshair arm).
    """

    arm_thickness: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["style_type"] = "CrossHairPointStyle"
        if self.arm_thickness is not None:
            result["arm_thickness"] = self.arm_thickness
        return result
