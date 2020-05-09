# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Simple script to lift any temporary bans that have expired.

This script should be set up to run regularly (such as every hour).
"""

from tildes.lib.database import get_session_from_config
from tildes.lib.datetime import utc_now
from tildes.models.user import User


def lift_expired_temporary_bans(config_path: str) -> None:
    """Lift temporary bans that have expired."""
    db_session = get_session_from_config(config_path)

    db_session.query(User).filter(
        User.ban_expiry_time < utc_now(),  # type: ignore
        User.is_banned == True,  # noqa
    ).update({"is_banned": False, "ban_expiry_time": None}, synchronize_session=False)

    db_session.commit()
