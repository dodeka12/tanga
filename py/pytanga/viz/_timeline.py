# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Timeline — fluent builder for sequenced keyframe animations."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .visualizer import Visualizer


class Timeline:
    """Fluent builder for sequenced keyframe animations.

    Builds a series of timed animation steps and sends them to the browser
    as a single ``timeline`` WebSocket message. The browser staggers each
    step via ``setTimeout``.

    Usage::

        viz.timeline()
           .animate_to(pt_id, position=(5, 0, 0), duration=1.5, easing="ease-in-out")
           .wait(0.3)
           .animate_to(sph_id, opacity=0.1, duration=2)
           .play()

    ``parallel=True`` makes a step run concurrently with the previous one::

        viz.timeline()
           .animate_to(pt_a, position=(3, 0, 0), duration=1)
           .animate_to(pt_b, position=(0, 3, 0), duration=1, parallel=True)
           .play()
    """

    def __init__(self, visualizer: Visualizer, *, scene_name: str = "") -> None:
        self._viz = visualizer
        self._scene_name = scene_name
        self._steps: list[dict[str, Any]] = []
        self._current_time: float = 0.0

    def wait(self, seconds: float) -> Timeline:
        """Insert a gap of ``seconds`` before the next animation step."""
        self._current_time += seconds
        return self

    def animate_to(
        self,
        entity_id: str,
        *,
        position: tuple[float, float, float] | None = None,
        rotation: tuple[float, float, float] | None = None,
        opacity: float | None = None,
        scale: tuple[float, float, float] | None = None,
        duration: float = 1.0,
        easing: str = "ease-in-out",
        parallel: bool = False,
    ) -> Timeline:
        """Add an animation step to the timeline.

        Args:
            entity_id: Entity ID to animate.
            position: Target world-space position.
            rotation: Target Euler rotation in radians.
            opacity: Target opacity ``0.0..1.0``.
            scale: Target scale.
            duration: Animation duration in seconds.
            easing: One of ``"linear"``, ``"ease-in"``, ``"ease-out"``,
                ``"ease-in-out"``.
            parallel: If ``True``, this step starts at the same time as the
                previous step rather than after it.
        """
        target: dict[str, Any] = {}
        if position is not None:
            target["position"] = list(position)
        if rotation is not None:
            target["rotation"] = list(rotation)
        if opacity is not None:
            target["opacity"] = float(opacity)
        if scale is not None:
            target["scale"] = list(scale)

        if not target:
            return self  # nothing to animate, skip silently

        if not parallel:
            # Tiny gap to prevent overlapping tweens on the same entity
            self._current_time += 0.01

        self._steps.append(
            {
                "at": self._current_time,
                "animate": {
                    "id": entity_id,
                    "target": target,
                    "duration": duration,
                    "easing": easing,
                },
            }
        )

        if not parallel:
            self._current_time += duration

        return self

    def play(self) -> None:
        """Send the assembled timeline to the browser for execution."""
        if not self._steps:
            return

        msg: dict[str, Any] = {
            "type": "timeline",
            "steps": self._steps,
        }
        if self._scene_name:
            msg["scene"] = self._scene_name
        message = json.dumps(msg)
        self._viz._send_raw(message)
