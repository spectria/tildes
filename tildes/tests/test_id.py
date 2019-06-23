# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for ID-related functions."""

from pytest import raises

from tildes.lib.id import id36_to_id, id_to_id36


def test_id_to_id36():
    """Make sure an ID->ID36 conversion is correct."""
    assert id_to_id36(571049189) == "9fzkdh"


def test_id36_to_id():
    """Make sure an ID36->ID conversion is correct."""
    assert id36_to_id("x48l4z") == 2002502915


def test_reversed_conversion_from_id():
    """Make sure an ID->ID36->ID conversion returns to original value."""
    original = 48102983
    assert id36_to_id(id_to_id36(original)) == original


def test_reversed_conversion_from_id36():
    """Make sure an ID36->ID->ID36 conversion returns to original value."""
    original = "h2l4pe"
    assert id_to_id36(id36_to_id(original)) == original


def test_zero_id_conversion_blocked():
    """Ensure the ID conversion function doesn't accept zero."""
    with raises(ValueError):
        id_to_id36(0)


def test_zero_id36_conversion_blocked():
    """Ensure the ID36 conversion function doesn't accept zero."""
    with raises(ValueError):
        id36_to_id("0")


def test_negative_id_conversion_blocked():
    """Ensure the ID conversion function doesn't accept negative numbers."""
    with raises(ValueError):
        id_to_id36(-1)


def test_negative_id36_conversion_blocked():
    """Ensure the ID36 conversion function doesn't accept negative numbers."""
    with raises(ValueError):
        id36_to_id("-1")
