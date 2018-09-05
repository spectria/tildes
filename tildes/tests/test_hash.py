# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from tildes.lib.hash import hash_string, is_match_for_hash


def test_same_string_verifies():
    """Ensure that the same string will match the hashed result."""
    string = "hunter2"
    hashed = hash_string(string)
    assert is_match_for_hash(string, hashed)


def test_different_string_fails():
    """Ensure that a different string doesn't match the hash."""
    string = "correct horse battery staple"
    wrong_string = "incorrect horse battery staple"

    hashed = hash_string(string)
    assert not is_match_for_hash(wrong_string, hashed)
