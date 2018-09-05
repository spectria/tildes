# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the base DatabaseModel class."""

from typing import Any, Optional, Type, TypeVar

from marshmallow import Schema
from sqlalchemy import event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import MetaData
from sqlalchemy.sql.schema import Table


ModelType = TypeVar("ModelType")  # pylint: disable=invalid-name

# SQLAlchemy naming convention for constraints and indexes
NAMING_CONVENTION = {
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
}


def attach_set_listener(
    class_: Type["DatabaseModelBase"], attribute: str, instance: "DatabaseModelBase"
) -> None:
    """Attach the SQLAlchemy ORM "set" attribute listener."""
    # pylint: disable=unused-argument
    def set_handler(
        target: "DatabaseModelBase", value: Any, oldvalue: Any, initiator: Any
    ) -> Any:
        """Handle an SQLAlchemy ORM "set" attribute event."""
        # pylint: disable=protected-access
        return target._validate_new_value(attribute, value)

    event.listen(instance, "set", set_handler, retval=True)


class DatabaseModelBase:
    """Base class for models that will persist to the database."""

    # declare the type of __table__ so mypy understands it when checking __eq__
    __table__: Table

    schema_class: Optional[Type[Schema]] = None

    def __eq__(self, other: Any) -> bool:
        """Equality comparison method - check if primary key values match."""
        if not isinstance(other, self.__class__):
            return NotImplemented

        # loop over all the columns in the primary key - if any don't match, return
        # False, otherwise return True if we get through all of them
        for column in self.__table__.primary_key:
            if getattr(self, column.name) != getattr(other, column.name):
                return False

        return True

    def __hash__(self) -> int:
        """Return the hash value of the model.

        This is implemented by mixing together the hash values of the primary key
        columns used in __eq__, as recommended in the Python documentation.
        """
        primary_key_values = tuple(
            getattr(self, column.name) for column in self.__table__.primary_key
        )
        return hash(primary_key_values)

    @property
    def schema(self) -> Schema:
        """Return a "partial" instance of the model's schema."""
        if not self.schema_class:
            raise AttributeError

        if not hasattr(self, "_schema"):
            self._schema = self.schema_class(partial=True)  # noqa

        return self._schema

    def _validate_new_value(self, attribute: str, value: Any) -> Any:
        """Validate the new value for a column.

        This function will be attached to the SQLAlchemy ORM attribute event for "set"
        and will be called whenever a new value is assigned to any of a model's column
        attributes. It works by deserializing/loading the new value through the
        marshmallow schema associated with the model class (by its `schema` class
        attribute).

        The deserialization process can modify the value if desired (for sanitization),
        or raise an exception which will prevent the assignment from happening at all.

        Note that if the schema does not have a Field defined for the column, or the
        Field is declared dump_only, no validation/sanitization will be applied.
        """
        if not self.schema_class:
            return value

        # This is a bit "magic", but simplifies the interaction between this validation
        # and SQLAlchemy hybrid properties. If the attribute being set starts with an
        # underscore, assume that it's due to being set up as a hybrid property, and
        # remove the underscore prefix when looking for a field to validate against.
        if attribute.startswith("_"):
            attribute = attribute[1:]

        field = self.schema.fields.get(attribute)

        if not field or field.dump_only:
            return value

        result = self.schema.load({attribute: value})
        return result.data[attribute]


DatabaseModel = declarative_base(
    cls=DatabaseModelBase,
    name="DatabaseModel",
    metadata=MetaData(naming_convention=NAMING_CONVENTION),
)


# attach the listener for SQLAlchemy ORM attribute "set" events to all models
event.listen(DatabaseModel, "attribute_instrument", attach_set_listener)
