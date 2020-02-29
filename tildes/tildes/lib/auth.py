# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions to help with authorization, such as generating ACLs."""

from typing import List, Optional

from pyramid.security import Allow, Deny

from tildes.typing import AceType


def aces_for_permission(
    required_permission: str,
    group_id: Optional[int] = None,
    granted_permission: Optional[str] = None,
) -> List[AceType]:
    """Return the ACEs for manually-granted (or denied) entries in UserPermissions."""
    aces = []

    # If the granted permission wasn't specified, use the required one without the type.
    # So if required is "topic.lock", the granted permission defaults to "lock".
    if granted_permission is None:
        granted_permission = required_permission.split(".", maxsplit=1)[1]

    contexts = ["*"]
    if group_id is not None:
        contexts.append(str(group_id))

    # add Deny entries first
    for context in contexts:
        aces.append((Deny, f"{context}:!{required_permission}", granted_permission))

    # then Allow entries
    for context in contexts:
        aces.append((Allow, f"{context}:{required_permission}", granted_permission))

    return aces
