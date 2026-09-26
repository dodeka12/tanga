# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Unit tests for the ``ProgressBar`` control and ``ProgressBarView``."""

from __future__ import annotations

from pytanga.viz import ProgressBarView
from pytanga.viz._controls import ProgressBar


# ── Test: ProgressBar model ────────────────────────────────────


def test_progress_bar_defaults() -> None:
    ctrl = ProgressBar(id="p")
    assert (ctrl.title, ctrl.value, ctrl.total, ctrl.indeterminate, ctrl.text) == (
        "",
        0.0,
        0,
        False,
        "",
    )


def test_progress_bar_serialize_fields() -> None:
    ctrl = ProgressBar(
        id="p", title="T", value=3.0, total=10, indeterminate=False, text="hi"
    )
    s = ctrl.serialize()
    assert s["kind"] == "progress"
    assert s["title"] == "T"
    assert s["value"] == 3.0
    assert s["total"] == 10
    assert s["indeterminate"] is False
    assert s["text"] == "hi"


def test_set_value_number_coerces_float() -> None:
    ctrl = ProgressBar(id="p", total=10)
    ctrl.set_value(4)
    assert ctrl.value == 4.0
    assert ctrl.get_value()["value"] == 4.0


def test_set_value_dict_updates_present_keys_only() -> None:
    ctrl = ProgressBar(id="p", title="Old")
    ctrl.set_value({"value": 5, "text": "step"})
    assert ctrl.value == 5.0
    assert ctrl.text == "step"
    # Keys omitted from the dict are left untouched.
    assert ctrl.title == "Old"
    assert ctrl.total == 0
    assert ctrl.indeterminate is False


def test_get_value_returns_full_dict() -> None:
    ctrl = ProgressBar(
        id="p", title="T", value=2.5, total=8, indeterminate=True, text="x"
    )
    assert ctrl.get_value() == {
        "title": "T",
        "value": 2.5,
        "total": 8,
        "indeterminate": True,
        "text": "x",
    }


def test_handle_event_change_is_pass_through() -> None:
    ctrl = ProgressBar(id="p", value=1.0)
    d = ctrl.handle_event("change", {"value": 7})
    assert (d.event, d.value, d.push) == ("change", 7, None)
    assert ctrl.value == 1.0  # generic dispatch does not mutate the model


# ── Test: ProgressBarView ──────────────────────────────────────


def test_view_serialize_type_and_fields() -> None:
    view = ProgressBarView("p", title="T", value=3.0, total=10, text="hi")
    s = view._serialize()
    assert s["type"] == "progress_bar_view"
    assert s["title"] == "T"
    assert s["value"] == 3.0
    assert s["total"] == 10
    assert s["indeterminate"] is False
    assert s["text"] == "hi"


def test_view_push_methods_push_full_dict() -> None:
    view = ProgressBarView("p", total=10)
    pushed: list[tuple] = []
    view._push = lambda vid, value: pushed.append((vid, value))

    view.set_progress(5, "step")
    view.set_total(20)
    view.set_indeterminate(True)
    view.set_text("busy")
    view.reset()

    assert pushed[-1] == (
        "p",
        {"title": "", "value": 0.0, "total": 20, "indeterminate": True, "text": "busy"},
    )


def test_view_set_value_pushes_full_dict() -> None:
    view = ProgressBarView("p", total=10)
    pushed: list[tuple] = []
    view._push = lambda vid, value: pushed.append((vid, value))

    view.set_value(4)

    assert pushed == [
        (
            "p",
            {"title": "", "value": 4.0, "total": 10, "indeterminate": False, "text": ""},
        )
    ]


def test_view_start_stop_reset() -> None:
    view = ProgressBarView("p")
    view.start()
    assert view.control.indeterminate is True
    view.stop()
    assert view.control.indeterminate is False


def test_control_to_view_wraps_progress_bar() -> None:
    from pytanga.viz.views import control_to_view

    ctrl = ProgressBar(id="p", title="T", total=5)
    view = control_to_view(ctrl)
    assert isinstance(view, ProgressBarView)
    assert view.control is ctrl
