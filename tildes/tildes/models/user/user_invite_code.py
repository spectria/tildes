# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the UserInviteCode class."""

import random
import string
from datetime import datetime

from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Text, TIMESTAMP
from sqlalchemy.sql.expression import text

from tildes.lib.string import separate_string
from tildes.models import DatabaseModel

from .user import User


class UserInviteCode(DatabaseModel):
    """Model for invite codes that allow new users to register."""

    __tablename__ = "user_invite_codes"

    # the character set to generate codes using
    ALPHABET = string.ascii_uppercase + string.digits

    LENGTH = 15

    code: str = Column(
        Text,
        CheckConstraint(f"LENGTH(code) <= {LENGTH}", name="code_length"),
        primary_key=True,
    )
    user_id: int = Column(
        Integer, ForeignKey("users.user_id"), nullable=False, index=True
    )
    created_time: datetime = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    invitee_id: int = Column(Integer, ForeignKey("users.user_id"))

    def __str__(self) -> str:
        """Format the code into a more easily readable version."""
        return separate_string(self.code, "-", 5)

    def __init__(self, user: User):
        """Create a new (random) invite code owned by the user.

        Note that uniqueness is not confirmed here, so there is the potential to create
        duplicate codes (which will fail to commit to the database).
        """
        self.user_id = user.user_id

        code_chars = random.choices(self.ALPHABET, k=self.LENGTH)
        self.code = "".join(code_chars)

    @classmethod
    def prepare_code_for_lookup(cls, code: str) -> str:
        """Prepare/sanitize a code for lookup purposes."""
        # codes are stored in uppercase
        code = code.upper()

        # remove any characters that aren't in the code alphabet (allows dashes, spaces,
        # etc. to be used to make the codes more readable)
        code = "".join(letter for letter in code if letter in cls.ALPHABET)

        if len(code) > cls.LENGTH:
            raise ValueError("Code is longer than the maximum length")

        return code
