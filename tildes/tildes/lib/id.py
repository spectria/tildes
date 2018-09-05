# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Library code related to IDs, ID36s, and so on."""

import re
import string


ID36_REGEX = re.compile("^[a-z0-9]+$", re.IGNORECASE)


def id_to_id36(id_val: int) -> str:
    """Convert an integer ID to the string ID36 representation."""
    if id_val < 1:
        raise ValueError("ID values should never be zero or negative")

    reversed_chars = []

    # the "alphabet" of our ID36s - 0-9 followed by a-z
    alphabet = string.digits + string.ascii_lowercase

    # Repeatedly use divmod() on the value, which returns the quotient and remainder of
    # each integer division - divmod(a, b) == (a // b, a % b). The remainder of each
    # division works as an index into the alphabet, and doing this repeatedly will build
    # up our ID36 string in reverse order (with the least-significant "digit" first).
    quotient, index = divmod(id_val, 36)
    while quotient != 0:
        reversed_chars.append(alphabet[index])
        quotient, index = divmod(quotient, 36)
    reversed_chars.append(alphabet[index])

    # join the characters in reversed order and return as the result
    return "".join(reversed(reversed_chars))


def id36_to_id(id36_val: str) -> int:
    """Convert a string ID36 to the integer ID representation."""
    if id36_val.startswith("-") or id36_val == "0":
        raise ValueError("ID values should never be zero or negative")

    # Python's stdlib can handle this, much simpler in this direction
    return int(id36_val, 36)
