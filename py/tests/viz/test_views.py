# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the declarative view/layout model (`views.py`)."""

import pytest

from pytanga.viz import EAnchor
from pytanga.viz._controls import EControlVariant
from pytanga.viz._size import Size
from pytanga.viz.views import (
    ButtonView,
    CheckboxView,
    ColorPickerView,
    DropdownView,
    GroupView,
    MenuView,
    SceneView,
    SliderView,
    SpacerView,
    SplitView,
    StackView,
    TableView,
    TextAreaView,
    TextFieldView,
    ValueEditView,
    View,
    iter_scene_names,
    serialize_layout,
)


class _Handle:
    """Minimal stand-in for a ``VizSceneHandle``/``Scene`` with a ``name``."""

    name = "xyz"


class TestViewBase:
    def test_size_sets_both_preferred(self):
        v = View(size=Size.px(250))
        assert v.preferred_width == Size.px(250)
        assert v.preferred_height == Size.px(250)

    def test_size_does_not_override_explicit_preferred(self):
        v = View(size=Size.px(250), preferred_width=Size.percent(50))
        assert v.preferred_width == Size.percent(50)
        assert v.preferred_height == Size.px(250)

    def test_fixed_x(self):
        assert View(min_width=Size.px(200), max_width=Size.px(200)).fixed_x

    def test_not_fixed_x_when_only_min(self):
        assert not View(min_width=Size.px(200)).fixed_x

    def test_not_fixed_x_when_min_max_differ(self):
        assert not View(min_width=Size.px(100), max_width=Size.px(200)).fixed_x

    def test_fixed_y(self):
        assert View(min_height=Size.px(100), max_height=Size.px(100)).fixed_y


class TestSceneView:
    def test_scene_from_string(self):
        assert SceneView("main").scene == "main"

    def test_scene_from_handle(self):
        assert SceneView(_Handle()).scene == "xyz"

    def test_scene_rejects_bare_object(self):
        with pytest.raises(TypeError, match="scene name or handle"):
            SceneView(object())

    def test_default_min_size(self):
        assert SceneView("main").min_width == Size.px(120)
        assert SceneView("main").min_height == Size.px(120)

    def test_min_override(self):
        v = SceneView("main", min_width=Size.px(50))
        assert v.min_width == Size.px(50)
        assert v.min_height == Size.px(120)

    def test_min_disable(self):
        v = SceneView("main", min_width=None, min_height=None)
        assert v.min_width is None
        assert v.min_height is None

    def test_overlay_serialize(self):
        node = serialize_layout(SceneView("main", overlay=[GroupView("Actions")]))[
            "root"
        ]
        assert node["scene"] == "main"
        assert node["children"][0]["type"] == "group"
        assert node["children"][0]["title"] == "Actions"

    def test_no_overlay_omits_children(self):
        node = serialize_layout(SceneView("main"))["root"]
        assert "children" not in node

    def test_camera_serialize(self):
        from pytanga.viz.camera import CameraConfig3d

        node = serialize_layout(
            SceneView(
                "main", camera=CameraConfig3d(position=(1, 2, 3), target=(0, 0, 0))
            )
        )["root"]
        assert node["camera"]["type"] == "3d"
        assert node["camera"]["position"] == [1.0, 2.0, 3.0]
        assert node["camera"]["target"] == [0.0, 0.0, 0.0]

    def test_camera_normalizes_view_config(self):
        from pytanga.viz.camera import View3dConfig

        v = SceneView(
            "main",
            camera=View3dConfig(
                point=(0, 0, 0), normal=(0, 0, 1), extent_u=2, extent_v=2
            ),
        )
        assert v.camera.type == "3d"
        assert v.camera.position is not None
        assert v.camera.target == (0.0, 0.0, 0.0)

    def test_no_camera_omits_key(self):
        node = serialize_layout(SceneView("main"))["root"]
        assert "camera" not in node

    def test_auto_id_assigned_and_serialized(self):
        v = SceneView("main")
        assert isinstance(v.id, str) and v.id
        assert serialize_layout(v)["root"]["id"] == v.id

    def test_explicit_id(self):
        v = SceneView("main", id="top")
        assert v.id == "top"
        assert serialize_layout(v)["root"]["id"] == "top"

    def test_auto_ids_unique(self):
        assert SceneView("a").id != SceneView("b").id


class TestGroupView:
    def test_defaults(self):
        g = GroupView("Actions")
        assert g.title == "Actions"
        assert g.direction == "vertical"
        assert g.position is None
        assert g.collapsed is False
        assert g.children == []

    def test_children_and_options(self):
        g = GroupView(
            "Actions",
            [SpacerView()],
            direction="horizontal",
            position="bottom-right",
            collapsed=True,
        )
        assert g.direction == "horizontal"
        assert g.position == "bottom-right"
        assert g.collapsed is True
        assert len(g.children) == 1

    def test_serialize(self):
        node = serialize_layout(GroupView("Actions", [SpacerView()]))["root"]
        assert node["type"] == "group"
        assert node["title"] == "Actions"
        assert node["direction"] == "vertical"
        assert node["position"] is None
        assert node["collapsed"] is False
        assert node["children"][0]["type"] == "spacer"

    def test_scrollable_serialize(self):
        assert serialize_layout(GroupView("Actions"))["root"]["scrollable"] is False
        assert (
            serialize_layout(GroupView("Actions", scrollable=True))["root"][
                "scrollable"
            ]
            is True
        )

    def test_serialize_icon(self):
        node = serialize_layout(GroupView("Actions", icon="material:settings"))["root"]
        assert node["icon"] == "material:settings"
        assert node["icon_only"] is False

    def test_serialize_icon_omitted_when_none(self):
        node = serialize_layout(GroupView("Actions"))["root"]
        assert "icon" not in node

    def test_serialize_icon_only(self):
        node = serialize_layout(
            GroupView("Actions", icon="material:settings", icon_only=True)
        )["root"]
        assert node["icon"] == "material:settings"
        assert node["icon_only"] is True

    def test_serialize_parent_id(self):
        node = serialize_layout(GroupView("Actions", parent_id="sphere"))["root"]
        assert node["parent_id"] == "sphere"

    def test_serialize_parent_id_omitted_when_none(self):
        node = serialize_layout(GroupView("Actions"))["root"]
        assert "parent_id" not in node


class TestMenuView:
    def test_serialize_fields(self):
        node = serialize_layout(MenuView("Actions", [ButtonView("b1", label="Go")]))[
            "root"
        ]
        assert node["type"] == "menu"
        assert node["trigger_icon"] is None
        assert node["label"] == "Actions"
        assert node["mode"] == "dropdown"
        assert node["direction"] == "vertical"
        assert node["position"] is None
        assert node["children"][0]["type"] == "button_view"

    def test_serialize_custom_trigger_icon(self):
        node = serialize_layout(MenuView("Actions", trigger_icon="material:settings"))[
            "root"
        ]
        assert node["trigger_icon"] == "material:settings"

    def test_serialize_nested_child(self):
        sub = MenuView("Sub", [SliderView("s1")])
        node = serialize_layout(MenuView("Root", [sub]))["root"]
        assert node["children"][0]["type"] == "menu"
        assert node["children"][0]["label"] == "Sub"

    def test_serialize_bar_mode(self):
        node = serialize_layout(
            MenuView("Bar", mode="bar", direction="horizontal", position="top-right")
        )["root"]
        assert node["mode"] == "bar"
        assert node["direction"] == "horizontal"
        assert node["position"] == "top-right"

    def test_bar_defaults_to_horizontal_direction(self):
        node = serialize_layout(MenuView("Bar", mode="bar"))["root"]
        assert node["direction"] == "horizontal"

    def test_mode_validation(self):
        with pytest.raises(ValueError, match="mode"):
            MenuView("Menu", mode="popup")

    def test_direction_validation(self):
        with pytest.raises(ValueError, match="direction"):
            MenuView("Menu", direction="diagonal")

    def test_override_variant_forces_menu(self):
        menu = MenuView(
            "Menu",
            [
                ButtonView("b1", label="Go"),
                SliderView("s1", label="S"),
                CheckboxView("c1", label="C"),
            ],
        )
        node = serialize_layout(menu)["root"]
        assert [child["variant"] for child in node["children"]] == [
            "menu",
            "menu",
            "menu",
        ]

    def test_override_variant_disabled(self):
        menu = MenuView("Menu", [ButtonView("b1", label="Go")], override_variant=False)
        node = serialize_layout(menu)["root"]
        assert node["children"][0]["variant"] == "default"

    def test_override_variant_recurses_into_submenu(self):
        menu = MenuView("Menu", [MenuView("Sub", [ButtonView("b1", label="Go")])])
        node = serialize_layout(menu)["root"]
        assert node["children"][0]["type"] == "menu"
        assert node["children"][0]["children"][0]["variant"] == "menu"


class TestEAnchor:
    def test_anchor_values(self):
        assert [a.value for a in EAnchor] == [
            "top-left",
            "top-right",
            "bottom-left",
            "bottom-right",
            "top",
            "bottom",
            "left",
            "right",
        ]

    def test_group_view_serializes_anchor(self):
        node = serialize_layout(GroupView("G", position=EAnchor.TOP_RIGHT))["root"]
        assert node["position"] == "top-right"

    def test_menu_view_serializes_anchor(self):
        node = serialize_layout(MenuView("M", position=EAnchor.BOTTOM_LEFT))["root"]
        assert node["position"] == "bottom-left"


class TestControlViews:
    def test_slider_serialize(self):
        s = SliderView("s1", label="Radius", min=0.0, max=5.0, step=0.1, value=2.0)
        node = serialize_layout(s)["root"]
        assert node["type"] == "slider_view"
        assert node["id"] == "s1"
        assert node["label"] == "Radius"
        assert node["min"] == 0.0
        assert node["max"] == 5.0
        assert node["step"] == 0.1
        assert node["value"] == 2.0

    def test_slider_value_defaults_to_min(self):
        assert SliderView("s1", min=1.0, max=3.0).value == 1.0

    def test_button_serialize(self):
        node = serialize_layout(ButtonView("b1", label="Go"))["root"]
        assert node["type"] == "button_view"
        assert node["id"] == "b1"
        assert node["label"] == "Go"

    def test_dropdown_serialize(self):
        node = serialize_layout(
            DropdownView("d1", label="Mode", options=["a", "b"], value="a")
        )["root"]
        assert node["type"] == "dropdown_view"
        assert node["options"] == ["a", "b"]
        assert node["value"] == "a"

    def test_button_serialize_with_icon(self):
        node = serialize_layout(
            ButtonView("b1", label="Go", icon="material:refresh", icon_only=True)
        )["root"]
        assert node["type"] == "button_view"
        assert node["icon"] == "material:refresh"
        assert node["icon_only"] is True

    def test_button_variant_serialize(self):
        node = serialize_layout(
            ButtonView("b1", label="Go", variant=EControlVariant.MENU)
        )["root"]
        assert node["type"] == "button_view"
        assert node["variant"] == "menu"

    def test_button_variant_defaults_to_default(self):
        node = serialize_layout(ButtonView("b1", label="Go"))["root"]
        assert node["variant"] == "default"

    def test_text_field_serialize(self):
        node = serialize_layout(
            TextFieldView("t1", label="Name", value="a", placeholder="…")
        )["root"]
        assert node["type"] == "text_field_view"
        assert node["id"] == "t1"
        assert node["label"] == "Name"
        assert node["value"] == "a"
        assert node["placeholder"] == "…"

    def test_text_area_serialize(self):
        node = serialize_layout(TextAreaView("ta1", label="Notes", rows=6))["root"]
        assert node["type"] == "text_area_view"
        assert node["rows"] == 6

    def test_color_picker_serialize(self):
        node = serialize_layout(ColorPickerView("c1", label="Color", value="#ff0000"))[
            "root"
        ]
        assert node["type"] == "color_picker_view"
        assert node["value"] == "#ff0000"

    def test_checkbox_serialize(self):
        node = serialize_layout(CheckboxView("cb1", label="Wireframe", value=True))[
            "root"
        ]
        assert node["type"] == "checkbox_view"
        assert node["value"] is True

    def test_value_edit_serialize(self):
        node = serialize_layout(
            ValueEditView(
                "v1", label="Zoom", min=0.5, max=4.0, step=0.25, digits=2, value=1.5
            )
        )["root"]
        assert node["type"] == "value_edit_view"
        assert node["id"] == "v1"
        assert node["min"] == 0.5
        assert node["max"] == 4.0
        assert node["step"] == 0.25
        assert node["digits"] == 2
        assert node["value"] == 1.5
        assert node["editable"] is True

    def test_control_tooltip_serialize(self):
        node = serialize_layout(SliderView("s1", tooltip="hover"))["root"]
        assert node["tooltip"] == "hover"

    def test_table_view_serialize(self):
        node = serialize_layout(
            TableView(
                "tbl",
                label="Data",
                columns=["x", "y"],
                rows=[["1", "2"], ["3", "4"]],
            )
        )["root"]
        assert node["type"] == "table_view"
        assert node["id"] == "tbl"
        assert node["label"] == "Data"
        assert node["columns"] == ["x", "y"]
        assert node["rows"] == [["1", "2"], ["3", "4"]]
        assert node["allow_add_rows"] is True
        assert node["allow_add_columns"] is True


def test_table_view_set_control_value() -> None:
    from pytanga.viz._controls import set_control_value

    view = TableView("tbl", columns=["x"], rows=[["1"]])
    set_control_value(view.control, {"columns": ["y", "z"], "rows": [[2], [3]]})
    assert view.columns == ["y", "z"]
    assert view.rows == [["2"], ["3"]]


def test_view_serialize_matches_control_fields() -> None:
    from pytanga.viz._controls import Slider, _serialize_one_control

    view = SliderView("s1", label="Radius", min=0.0, max=5.0, step=0.1, value=2.0)
    node = serialize_layout(view)["root"]
    panel = _serialize_one_control(
        Slider(id="s1", label="Radius", min=0.0, max=5.0, step=0.1, value=2.0)
    )
    for key, val in panel.items():
        if key != "kind":
            assert node[key] == val


class TestStackView:
    def test_direction_validation(self):
        with pytest.raises(ValueError, match="direction"):
            StackView("diagonal")

    def test_allows_empty_children(self):
        assert StackView("vertical").children == []

    def test_serialize(self):
        node = serialize_layout(StackView("horizontal", [SpacerView(), SpacerView()]))[
            "root"
        ]
        assert node["type"] == "stack"
        assert node["direction"] == "horizontal"
        assert len(node["children"]) == 2
        assert node["children"][0]["type"] == "spacer"

    def test_scrollable_serialize(self):
        assert serialize_layout(StackView("vertical"))["root"]["scrollable"] is False
        assert (
            serialize_layout(StackView("vertical", scrollable=True))["root"][
                "scrollable"
            ]
            is True
        )


class TestSplitView:
    def test_requires_two_children(self):
        with pytest.raises(ValueError, match="at least 2"):
            SplitView("horizontal", [SceneView("a")])

    def test_bad_orientation(self):
        with pytest.raises(ValueError, match="orientation"):
            SplitView("diagonal", [SceneView("a"), SceneView("b")])

    def test_sizes_length_mismatch(self):
        with pytest.raises(ValueError, match="sizes must match"):
            SplitView(
                "horizontal",
                [SceneView("a"), SceneView("b")],
                sizes=[Size.px(1)],
            )

    def test_accepts_arbitrary_child_count(self):
        # A single split holds any number of children (N − 1 splitters on the
        # frontend); only a lower bound of 2 is enforced here.
        layout = SplitView(
            "horizontal",
            [SceneView("a"), SpacerView(), SceneView("b"), SceneView("c")],
        )
        node = serialize_layout(layout)["root"]
        assert len(node["children"]) == 4
        assert node["sizes"] == [None, None, None, None]


class TestSerialize:
    def test_scene_view_shape(self):
        data = serialize_layout(SceneView("main"), name="demo")
        assert data["type"] == "view_layout"
        assert data["name"] == "demo"
        node = data["root"]
        assert node["type"] == "scene_view"
        assert node["scene"] == "main"
        assert node["min_width"] == {"value": 120.0, "unit": "px"}
        assert node["min_height"] == {"value": 120.0, "unit": "px"}
        assert node["preferred_width"] is None

    def test_nested_split_shape(self):
        layout = SplitView(
            orientation="horizontal",
            children=[
                SceneView("main"),
                SplitView(
                    orientation="vertical",
                    sizes=[Size.percent(70), Size.percent(30)],
                    children=[
                        SceneView("side"),
                        GroupView("Controls"),
                    ],
                ),
            ],
        )
        root = serialize_layout(layout)["root"]

        assert root["type"] == "split"
        assert root["orientation"] == "horizontal"
        assert root["movable"] is None
        assert root["sizes"] == [None, None]

        assert root["children"][0]["type"] == "scene_view"
        assert root["children"][0]["scene"] == "main"

        inner = root["children"][1]
        assert inner["orientation"] == "vertical"
        assert inner["sizes"] == [
            {"value": 70.0, "unit": "%"},
            {"value": 30.0, "unit": "%"},
        ]
        assert inner["children"][0]["type"] == "scene_view"
        assert inner["children"][0]["scene"] == "side"
        assert inner["children"][1]["type"] == "group"
        assert inner["children"][1]["title"] == "Controls"

    def test_three_children_serialize_in_order(self):
        layout = SplitView(
            orientation="horizontal",
            sizes=[Size.percent(25), Size.percent(50), Size.percent(25)],
            children=[SceneView("a"), SceneView("b"), SceneView("c")],
        )
        root = serialize_layout(layout)["root"]

        assert root["type"] == "split"
        assert root["orientation"] == "horizontal"
        assert root["sizes"] == [
            {"value": 25.0, "unit": "%"},
            {"value": 50.0, "unit": "%"},
            {"value": 25.0, "unit": "%"},
        ]
        assert [c["scene"] for c in root["children"]] == ["a", "b", "c"]
        assert all(c["type"] == "scene_view" for c in root["children"])

    def test_ids_are_unique_and_deterministic(self):
        layout = SplitView("horizontal", [SceneView("a"), SceneView("b"), SpacerView()])
        first = serialize_layout(layout)["root"]
        second = serialize_layout(layout)["root"]
        ids = [first["id"]] + [c["id"] for c in first["children"]]
        assert len(ids) == len(set(ids))
        assert [c["id"] for c in first["children"]] == [
            c["id"] for c in second["children"]
        ]

    def test_size_fields_serialize(self):
        node = serialize_layout(View(min_width=Size.px(100), max_width=Size.px(100)))[
            "root"
        ]
        assert node["min_width"] == {"value": 100.0, "unit": "px"}
        assert node["max_width"] == {"value": 100.0, "unit": "px"}
        assert node["min_height"] is None


class TestIterSceneNames:
    def test_dedup_and_order(self):
        layout = SplitView(
            "horizontal",
            [
                SceneView("main"),
                SplitView(
                    "vertical",
                    [
                        SceneView("side"),
                        SceneView("main"),  # duplicate reference
                        SceneView("extra"),
                    ],
                ),
            ],
        )
        assert iter_scene_names(layout) == ["main", "side", "extra"]

    def test_recurses_into_stack_and_overlay(self):
        layout = StackView(
            "vertical",
            [
                SceneView("a"),
                GroupView("g", [ButtonView("b1")]),
                SceneView("b", overlay=[GroupView("g2", [SliderView("s1")])]),
            ],
        )
        assert iter_scene_names(layout) == ["a", "b"]
