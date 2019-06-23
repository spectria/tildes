# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions/constants related to hashing."""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


# These parameter values were chosen to achieve a hash-verification time of about 10ms
# on the current production server. They can be updated to different values if the
# server changes (consider upgrading old password hashes on login as well if that
# happens).
ARGON2_TIME_COST = 4
ARGON2_MEMORY_COST = 8092

ARGON2_HASHER = PasswordHasher(
    time_cost=ARGON2_TIME_COST, memory_cost=ARGON2_MEMORY_COST
)


def hash_string(string: str) -> str:
    """Hash the string and return the hashed result."""
    return ARGON2_HASHER.hash(string)


def is_match_for_hash(string: str, hashed: str) -> bool:
    """Return whether a string is a match for the specified hash."""
    try:
        ARGON2_HASHER.verify(hashed, string)
    except VerifyMismatchError:
        return False

    return True
