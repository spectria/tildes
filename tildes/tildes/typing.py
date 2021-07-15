# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Custom type aliases to use in type annotations."""

from typing import Any

# types for an ACE (Access Control Entry), and the ACL (Access Control List) of them
AceType = tuple[str, Any, str]
AclType = list[AceType]
