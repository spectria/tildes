# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Constants/classes/functions related to the database."""

import enum
from typing import Any, Callable, List, Optional

from pyramid.paster import bootstrap
from sqlalchemy import cast, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.orm.session import Session
from sqlalchemy.types import UserDefinedType
from sqlalchemy_utils import LtreeType
from sqlalchemy_utils.types.ltree import LQUERY


# https://www.postgresql.org/docs/current/static/errcodes-appendix.html
NOT_NULL_ERROR_CODE = 23502


def get_session_from_config(config_path: str) -> Session:
    """Get a database session from a config file (specified by path)."""
    env = bootstrap(config_path)
    session_factory = env["registry"]["db_session_factory"]
    return session_factory()


class LockSpaces(enum.Enum):
    """Enum of valid options for "lock spaces" used for advisory locks."""

    GENERATE_INVITE_CODE = enum.auto()


def obtain_transaction_lock(
    session: Session, lock_space: Optional[str], lock_value: int
) -> None:
    """Obtain a transaction-level advisory lock from PostgreSQL.

    The lock_space arg must be either None or the name of one of the members of the
    LockSpaces enum (case-insensitive). Contention for a lock will only occur when both
    lock_space and lock_value have the same values.
    """
    if lock_space:
        try:
            lock_space_value = LockSpaces[lock_space.upper()].value
        except KeyError:
            raise ValueError("Invalid lock space: %s" % lock_space)

        session.query(func.pg_advisory_xact_lock(lock_space_value, lock_value)).one()
    else:
        session.query(func.pg_advisory_xact_lock(lock_value)).one()


class CIText(UserDefinedType):
    """PostgreSQL citext type for case-insensitive text values.

    For more info, see the docs:
    https://www.postgresql.org/docs/current/static/citext.html
    """

    python_type = str

    def get_col_spec(self, **kw: Any) -> str:
        """Return the type name (for creating columns and so on)."""
        # pylint: disable=no-self-use,unused-argument
        return "CITEXT"

    def bind_processor(self, dialect: Dialect) -> Callable:
        """Return a conversion function for processing bind values."""

        def process(value: Any) -> Any:
            return value

        return process

    def result_processor(self, dialect: Dialect, coltype: Any) -> Callable:
        """Return a conversion function for processing result row values."""

        def process(value: Any) -> Any:
            return value

        return process


class ArrayOfLtree(ARRAY):  # pylint: disable=too-many-ancestors
    """Workaround class to support ltree[] columns which don't work "normally".

    This is heavily based on the ArrayOfEnum class from the SQLAlchemy docs:
    http://docs.sqlalchemy.org/en/latest/dialects/postgresql.html#using-enum-with-array
    """

    def __init__(self) -> None:
        """Initialize as ARRAY(LtreeType)."""
        super().__init__(LtreeType)

    def bind_expression(self, bindvalue: Any) -> Any:
        """Convert bind value to an SQL expression."""
        return cast(bindvalue, self)

    def result_processor(self, dialect: Any, coltype: Any) -> Callable:
        """Return a conversion function for processing result row values."""
        super_rp = super().result_processor(dialect, coltype)

        def handle_raw_string(value: str) -> List[str]:
            if not (value.startswith("{") and value.endswith("}")):
                raise ValueError("%s is not an array value" % value)

            # trim off the surrounding braces
            value = value[1:-1]

            # if there's nothing left, return an empty list
            if not value:
                return []

            return value.split(",")

        def process(value: Optional[str]) -> Optional[List[str]]:
            if value is None:
                return None

            return super_rp(handle_raw_string(value))

        return process

    # pylint: disable=invalid-name,too-many-ancestors
    class comparator_factory(ARRAY.comparator_factory):
        """Add custom comparison functions.

        The ancestor_of, descendant_of, and lquery functions are supported by LtreeType,
        so this duplicates them here so they can be used on ArrayOfLtree too.
        """

        def ancestor_of(self, other):  # type: ignore
            """Return whether the array contains any ancestor of `other`."""
            return self.op("@>")(other)

        def descendant_of(self, other):  # type: ignore
            """Return whether the array contains any descendant of `other`."""
            return self.op("<@")(other)

        def lquery(self, other):  # type: ignore
            """Return whether the array matches the lquery/lqueries in `other`."""
            if isinstance(other, list):
                return self.op("?")(cast(other, ARRAY(LQUERY)))
            else:
                return self.op("~")(other)
