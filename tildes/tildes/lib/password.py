# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions/constants related to user passwords."""

from hashlib import sha1

from redis import ConnectionError, Redis, ResponseError  # noqa


# unix socket path for redis server with the breached passwords bloom filter
BREACHED_PASSWORDS_REDIS_SOCKET = "/run/redis_breached_passwords/socket"

# Key where the bloom filter of password hashes from data breaches is stored
BREACHED_PASSWORDS_BF_KEY = "breached_passwords_bloom"


def is_breached_password(password: str) -> bool:
    """Return whether the password is in the breached-passwords list."""
    redis = Redis(unix_socket_path=BREACHED_PASSWORDS_REDIS_SOCKET)

    hashed = sha1(password.encode("utf-8")).hexdigest()

    try:
        return bool(
            redis.execute_command("BF.EXISTS", BREACHED_PASSWORDS_BF_KEY, hashed)
        )
    except (ConnectionError, ResponseError):
        # server isn't running, bloom filter doesn't exist or the key is a different
        # data type
        return False
