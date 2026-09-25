# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Shared helpers, constants, and counters for the layout view model."""

from __future__ import annotations

from itertools import count
from typing import TYPE_CHECKING, Any

from .._size import Size, SizeSpec
from ..camera import CameraLock, Navigation

if TYPE_CHECKING:
    from .._scene_handle import VizSceneHandle
    from ..scene import Scene

    SceneRef = str | Scene | VizSceneHandle


#: Default minimum extent for a scene pane on both axes, so a scene can never
#: be collapsed to nothing (override per view, or pass ``None`` to disable).
_DEFAULT_SCENE_MIN = Size.px(120)

#: Per-column horizontal floor for :class:`TableView` (px), so an N-column grid
#: keeps every column visible inside an auto-sized overlay panel.
_TABLE_COLUMN_MIN_PX = 60

#: Default gap (px) between a separator line and the adjacent content.
_DEFAULT_SEPARATOR_SPACING = 6

#: Valid ``CameraView.lock`` values (``CameraLock`` member strings).
_LOCK_VALUES: frozenset[str] = frozenset(m.value for m in CameraLock)

#: Valid ``CameraView.navigation`` values (``Navigation`` member strings).
_NAVIGATION_VALUES: frozenset[str] = frozenset(n.value for n in Navigation)

#: Process-wide counter for auto-generated ``SceneView`` pane ids (``sv0``…).
_scene_view_counter = count()

#: Process-wide counter for auto-generated ``LogView`` ids (``log0``…).
_log_view_counter = count()

#: Process-wide counter for auto-generated ``View`` ids (``v0``…).
_view_counter = count()


def _size_dict(spec: SizeSpec) -> dict[str, Any] | None:
    """Serialize a ``SizeSpec`` to the canonical JSON shape (``None`` → ``null``)."""
    return None if spec is None else spec.to_dict()


def _coerce_scene_name(scene: SceneRef) -> str:
    """Accept a scene name string or an object exposing ``.name`` (handle/scene)."""
    if isinstance(scene, str):
        return scene
    name = getattr(scene, "name", None)
    if isinstance(name, str):
        return name
    raise TypeError(f"Expected a scene name or handle, got {type(scene).__name__}")


def _normalize_lock(lock: set[str] | None) -> set[str]:
    """Validate a ``CameraView.lock`` set and return it as a ``set``."""
    if lock is None:
        return set()
    result: set[str] = set()
    for value in lock:
        if value not in _LOCK_VALUES:
            raise ValueError(
                f"Invalid camera lock part {value!r}; "
                f"expected one of {sorted(_LOCK_VALUES)}"
            )
        result.add(value)
    return result


def _normalize_navigation(navigation: str | Navigation) -> str:
    """Validate a navigation mode and return its string value."""
    value = navigation.value if isinstance(navigation, Navigation) else navigation
    if value not in _NAVIGATION_VALUES:
        raise ValueError(
            f"navigation must be one of {sorted(_NAVIGATION_VALUES)}, "
            f"got {navigation!r}"
        )
    return value


def _image_meta(image: Any) -> dict[str, Any]:
    """Serialize an ``ImageData`` to the ``background_image`` metadata dict."""
    if image.source == "tiled":
        return image.tiled_meta
    meta: dict[str, Any] = {
        "id": image.id,
        "width": image.width,
        "height": image.height,
        "channels": image.channels,
        "dtype": int(image.dtype),
        "source": image.source,
    }
    if image.url is not None:
        meta["url"] = image.url
    return meta


def _normalize_id_set(values: set[str] | None) -> set[str]:
    """Validate a ``hide``/``show`` set of entity ids."""
    if values is None:
        return set()
    result: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value:
            raise ValueError("hide/show entries must be non-empty strings")
        result.add(value)
    return result
