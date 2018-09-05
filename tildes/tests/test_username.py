# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from itertools import product

from tildes.schemas.user import (
    is_valid_username,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
)


def test_too_short_invalid():
    """Ensure too-short username is invalid."""
    length = USERNAME_MIN_LENGTH - 1
    username = "x" * length

    assert not is_valid_username(username)


def test_too_long_invalid():
    """Ensure too-long username is invalid."""
    length = USERNAME_MAX_LENGTH + 1
    username = "x" * length

    assert not is_valid_username(username)


def test_valid_length_range():
    """Ensure the entire range of valid lengths work."""
    for length in range(USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH + 1):
        username = "x" * length
        assert is_valid_username(username)


def test_consecutive_spacer_chars_invalid():
    """Ensure that a username with consecutive "spacer chars" is invalid."""
    spacer_chars = "_-"

    for char1, char2 in product(spacer_chars, spacer_chars):
        username = f"abc{char1}{char2}xyz"
        assert not is_valid_username(username)


def test_typical_username_valid():
    """Ensure a "normal-looking" username is considered valid."""
    assert is_valid_username("someTypical_user-85")


def test_invalid_characters():
    """Ensure that invalid chars can't be included (not comprehensive)."""
    invalid_chars = ' ~!@#$%^&*()+={}[]|\\:;"<>,.?/'

    for char in invalid_chars:
        username = f"abc{char}xyz"
        assert not is_valid_username(username)


def test_unicode_characters():
    """Ensure that unicode chars can't be included (not comprehensive)."""
    for username in ("pokémon", "ポケモン", "møøse"):
        assert not is_valid_username(username)
