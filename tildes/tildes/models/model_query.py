# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the ModelQuery class, a specialized SQLAlchemy Query subclass."""
# pylint: disable=self-cls-assignment

from typing import Any, Iterator, TypeVar

from pyramid.request import Request
from sqlalchemy import event
from sqlalchemy.orm import Load, undefer
from sqlalchemy.orm.query import Query


ModelType = TypeVar("ModelType")


class ModelQuery(Query):
    """Class for querying models via request.query()."""

    def __init__(self, model_cls: Any, request: Request):
        """Initialize a ModelQuery for the specified model and request."""
        super().__init__(model_cls, session=request.db_session)

        self.model_cls = model_cls
        self.request = request

        # can only filter deleted items if the table has an 'is_deleted' column
        self.filter_deleted = bool("is_deleted" in model_cls.__table__.columns)

        # can only filter removed items if the table has an 'is_removed' column
        self.filter_removed = bool("is_removed" in model_cls.__table__.columns)

    def __iter__(self) -> Iterator[ModelType]:
        """Iterate over the (processed) results of the query.

        SQLAlchemy goes through __iter__ to execute the query and return the results, so
        adding processing here should cover all the possibilities.
        """
        results = super().__iter__()
        return iter([self._process_result(result) for result in results])

    def _attach_extra_data(self) -> "ModelQuery":
        """Override to attach extra data to query before execution."""
        return self

    def _finalize(self) -> "ModelQuery":
        """Finalize the query before it's executed."""
        # pylint: disable=protected-access

        # Assertions are disabled to allow these functions to add more filters even
        # though .limit() or .offset() may have already been called. This is potentially
        # dangerous, but should be fine with the existing straightforward usage
        # patterns.
        return (
            self.enable_assertions(False)
            ._attach_extra_data()
            ._filter_deleted_if_necessary()
            ._filter_removed_if_necessary()
        )

    def _before_compile_listener(self) -> "ModelQuery":
        """Do any final adjustments to the query before it's compiled.

        Note that this method cannot be overridden by subclasses because of the way it
        is subscribed to the event. Subclasses should override the _finalize() method
        instead if necessary.
        """
        return self._finalize()

    def _filter_deleted_if_necessary(self) -> "ModelQuery":
        """Filter out deleted rows unless they were explicitly included."""
        if not self.filter_deleted:
            return self

        return self.filter(self.model_cls.is_deleted == False)  # noqa

    def _filter_removed_if_necessary(self) -> "ModelQuery":
        """Filter out removed rows unless they were explicitly included."""
        if not self.filter_removed:
            return self

        return self.filter(self.model_cls.is_removed == False)  # noqa

    def lock_based_on_request_method(self) -> "ModelQuery":
        """Lock the rows if request method implies it's needed (generative).

        Applying this function to a query will cause the database to acquire a row-level
        FOR UPDATE lock on any rows the query retrieves. This is only done if the
        request method is DELETE, PATCH, or PUT, which all imply that the item(s) being
        fetched are going to be modified.

        Note that POST is specifically not included, because the item being POSTed to is
        not usually modified in a "dangerous" way as a result.
        """
        if self.request.method in {"DELETE", "PATCH", "PUT"}:
            return self.with_for_update(of=self.model_cls)

        return self

    def include_deleted(self) -> "ModelQuery":
        """Specify that deleted rows should be included (generative)."""
        self.filter_deleted = False

        return self

    def include_removed(self) -> "ModelQuery":
        """Specify that removed rows should be included (generative)."""
        self.filter_removed = False

        return self

    def join_all_relationships(self) -> "ModelQuery":
        """Eagerly join all lazy relationships (generative).

        This is useful for being able to load an item "fully" in a single query and
        avoid needing to make additional queries for related items.
        """
        self = self.options(Load(self.model_cls).joinedload("*"))

        return self

    def undefer_all_columns(self) -> "ModelQuery":
        """Undefer all columns (generative)."""
        self = self.options(undefer("*"))

        return self

    @staticmethod
    def _process_result(result: ModelType) -> ModelType:
        """Process a single result row (subclasses may need to override)."""
        return result


# add a listener so the _finalize() function will be called automatically just before
# the query executes
event.listen(
    ModelQuery,
    "before_compile",
    ModelQuery._before_compile_listener,  # pylint: disable=protected-access
    retval=True,
)
