# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions/constants related to user passwords."""

import subprocess
from hashlib import sha1

from tildes import settings
from tildes.metrics import summary_timer


@summary_timer("breached_password_check")
def is_breached_password(password: str) -> bool:
    """Return whether the password is in the breached-passwords list.

    Note: this function uses a binary-search utility on the breached-passwords file, so
    the file's format is not flexible. Each line of the file must begin with a single
    uppercase SHA-1 hash corresponding to a password that should be blocked, and the
    lines must be sorted in lexographical order.

    This is specifically intended for use with a "Pwned Passwords" list downloaded from
    https://haveibeenpwned.com/passwords (SHA-1 format, "ordered by hash"), but any
    other file with a compatible format will also work.
    """
    try:
        hash_list_path = settings.INI_FILE_SETTINGS["breached_passwords_hash_file_path"]
    except KeyError:
        return False

    hashed = sha1(password.encode("utf-8")).hexdigest().upper()

    # call pts_lbsearch in "prefix search" mode - exit code 0 means it found a match
    try:
        subprocess.run(["pts_lbsearch", "-p", hash_list_path, hashed], check=True)
    except subprocess.CalledProcessError:
        return False

    return True
