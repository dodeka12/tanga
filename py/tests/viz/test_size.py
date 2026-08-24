# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the split-view ``Size`` value type (`_size.py`)."""

import pytest

from pytanga.viz._size import Size, size_from_dict


class TestFactories:
    def test_px(self):
        assert Size.px(320) == Size(320, "px")

    def test_percent(self):
        assert Size.percent(50) == Size(50, "%")

    def test_fr(self):
        assert Size.fr(2) == Size(2, "fr")

    def test_auto(self):
        assert Size.auto() == Size(0.0, "auto")


class TestSerialize:
    @pytest.mark.parametrize(
        "size, expected",
        [
            (Size.px(320), {"value": 320.0, "unit": "px"}),
            (Size.percent(50), {"value": 50.0, "unit": "%"}),
            (Size.fr(2), {"value": 2.0, "unit": "fr"}),
            (Size.auto(), {"value": 0.0, "unit": "auto"}),
        ],
    )
    def test_to_dict(self, size, expected):
        assert size.to_dict() == expected

    @pytest.mark.parametrize(
        "data, expected",
        [
            ({"value": 320, "unit": "px"}, Size.px(320)),
            ({"value": 50, "unit": "%"}, Size.percent(50)),
            ({"value": 2, "unit": "fr"}, Size.fr(2)),
            ({"value": 0, "unit": "auto"}, Size.auto()),
            ({"value": 320}, Size.px(320)),  # unit defaults to px
        ],
    )
    def test_from_dict(self, data, expected):
        assert Size.from_dict(data) == expected

    def test_from_dict_rejects_non_dict(self):
        with pytest.raises(TypeError, match="Expected a dict"):
            Size.from_dict(5)

    def test_from_dict_rejects_missing_value(self):
        with pytest.raises(ValueError, match="numeric 'value'"):
            Size.from_dict({"unit": "px"})

    def test_unknown_unit(self):
        with pytest.raises(ValueError, match="Unknown size unit"):
            Size(1, "em")


class TestResolve:
    def test_px(self):
        assert Size.px(320).resolve(1000) == 320

    def test_percent(self):
        assert Size.percent(50).resolve(1000) == 500

    def test_fr_defers_to_natural(self):
        assert Size.fr(2).resolve(1000, natural=123) == 123

    def test_auto_defers_to_natural(self):
        assert Size.auto().resolve(1000, natural=None) is None


class TestHelpers:
    def test_clone_is_equal_but_distinct(self):
        s = Size.px(10)
        c = s.clone()
        assert c == s
        assert c is not s

    def test_immutability(self):
        s = Size.px(10)
        with pytest.raises(AttributeError):
            s.value = 20

    def test_size_from_dict_none(self):
        assert size_from_dict(None) is None

    def test_size_from_dict_size(self):
        assert size_from_dict({"value": 50, "unit": "%"}) == Size.percent(50)
