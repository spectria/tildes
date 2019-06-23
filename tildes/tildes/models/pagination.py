# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the PaginatedQuery and PaginatedResults classes."""

from itertools import chain
from typing import Any, Iterator, List, Optional, Sequence, TypeVar

from pyramid.request import Request
from sqlalchemy import Column, func, inspect

from tildes.lib.id import id36_to_id, id_to_id36

from .model_query import ModelQuery


ModelType = TypeVar("ModelType")


class PaginatedQuery(ModelQuery):
    """ModelQuery subclass that supports being split into pages."""

    def __init__(self, model_cls: Any, request: Request):
        """Initialize a PaginatedQuery for the specified model and request."""
        super().__init__(model_cls, request)

        # default to sorting by created_time descending (newest first)
        self._sort_column = model_cls.created_time
        self.sort_desc = True

        self.after_id: Optional[int] = None
        self.before_id: Optional[int] = None

        self._anchor_table = model_cls.__table__

    def __iter__(self) -> Iterator[ModelType]:
        """Iterate over the results of the query, reversed if necessary."""
        if not self.is_reversed:
            return super().__iter__()

        results: List[ModelType] = list(super().__iter__())

        return iter(reversed(results))

    @property
    def sorting_columns(self) -> List[Column]:
        """Return the columns being used for sorting."""
        if not self._sort_column:
            raise AttributeError

        if self.is_anchor_same_type:
            # add a final sort by the ID so keyset pagination works properly
            return [self._sort_column] + list(self.model_cls.__table__.primary_key)
        else:
            return [self._sort_column]

    @property
    def sorting_columns_desc(self) -> List[Column]:
        """Return descending versions of the sorting columns."""
        return [col.desc() for col in self.sorting_columns]

    @property
    def is_anchor_same_type(self) -> bool:
        """Return whether the anchor type is the same as the overall model_cls."""
        return self._anchor_table == self.model_cls.__table__

    @property
    def is_reversed(self) -> bool:
        """Return whether the query is operating "in reverse".

        This is a bit confusing. When moving "forward" through pages, items will be
        queried in the same order that they are displayed. For example, when displaying
        the newest topics, the query is simply for "newest N topics" (where N is the
        number of items per page), with an optional "after topic X" clause. Either way,
        the first result from the query will have the highest created_time, and should
        be the first item displayed.

        However, things work differently when you are paging "backwards". Since this is
        done by looking before a specific item, the query needs to fetch items in the
        opposite order of how they will be displayed. For the "newest" sort example,
        when paging backwards you need to query for "*oldest* N items before topic X",
        so the query ordering is the exact opposite of the desired display order. The
        first result from the query will have the *lowest* created_time, so should be
        the last item displayed. Because of this, the results need to be reversed.
        """
        return bool(self.before_id)

    def anchor_type(self, anchor_type: str) -> "PaginatedQuery":
        """Set the type of the "anchor" (before/after item) (generative)."""
        anchor_table_name = anchor_type + "s"
        self._anchor_table = self.model_cls.metadata.tables.get(anchor_table_name)

        return self

    def after_id36(self, id36: str) -> "PaginatedQuery":
        """Restrict the query to results after an id36 (generative)."""
        if self.before_id:
            raise ValueError("Can't set both before and after restrictions")

        self.after_id = id36_to_id(id36)

        return self

    def before_id36(self, id36: str) -> "PaginatedQuery":
        """Restrict the query to results before an id36 (generative)."""
        if self.after_id:
            raise ValueError("Can't set both before and after restrictions")

        self.before_id = id36_to_id(id36)

        return self

    def _apply_before_or_after(self) -> "PaginatedQuery":
        """Apply the "before" or "after" restrictions if necessary."""
        # pylint: disable=assignment-from-no-return
        if not (self.after_id or self.before_id):
            return self

        query = self

        # determine the ID of the "anchor item" that we're using as an upper or lower
        # bound, and which type of bound it is
        if self.after_id:
            anchor_id = self.after_id

            # since we're looking for other items "after" the anchor item, it will act
            # as an upper bound when the sort order is descending, otherwise it's a
            # lower bound
            is_anchor_upper_bound = self.sort_desc
        elif self.before_id:
            anchor_id = self.before_id

            # opposite of "after" behavior - when looking "before" the anchor item, it's
            # an upper bound if the sort order is *ascending*
            is_anchor_upper_bound = not self.sort_desc

        subquery = self._anchor_subquery(anchor_id)

        # restrict the results to items on the right "side" of the anchor item
        if is_anchor_upper_bound:
            query = query.filter(func.row(*self.sorting_columns) < subquery)
        else:
            query = query.filter(func.row(*self.sorting_columns) > subquery)

        return query

    def _anchor_subquery(self, anchor_id: int) -> Any:
        """Return a subquery to get comparison values for the anchor item."""
        if len(self._anchor_table.primary_key) > 1:
            raise TypeError("Only single-col primary key tables are supported")

        id_column = list(self._anchor_table.primary_key)[0]

        if self.is_anchor_same_type:
            columns = self.sorting_columns
        else:
            columns = [
                self._anchor_table.columns.get(column.name)
                for column in self.sorting_columns
            ]

        return (
            self.request.db_session.query(*columns)
            .filter(id_column == anchor_id)
            .subquery()
        )

    def _finalize(self) -> "PaginatedQuery":
        """Finalize the query before execution."""
        query = super()._finalize()

        # if the query is reversed, we need to sort in the opposite dir (basically
        # self.sort_desc XOR self.is_reversed)
        desc = self.sort_desc
        if self.is_reversed:
            desc = not desc

        if desc:
            query = query.order_by(*self.sorting_columns_desc)
        else:
            query = query.order_by(*self.sorting_columns)

        # pylint: disable=protected-access
        query = query._apply_before_or_after()

        return query

    def get_page(self, per_page: int) -> "PaginatedResults":
        """Get a page worth of results from the query (`per page` items)."""
        return PaginatedResults(self, per_page)


class PaginatedResults:
    """Results from a PaginatedQuery.

    Has a few extra attributes that give info about the pagination.
    """

    def __init__(self, query: PaginatedQuery, per_page: int):
        """Fetch results from a PaginatedQuery."""
        self.query = query
        self.per_page = per_page

        # if the query had `before` or `after` restrictions, there must be a page in
        # that direction (it's where we came from)
        self.has_next_page = bool(query.before_id)
        self.has_prev_page = bool(query.after_id)

        # fetch the results - try to get one more than we're actually going to display,
        # so that we know if there's another page
        self.results = query.limit(per_page + 1).all()

        # if we managed to get one more item than the page size, there's another page in
        # the same direction that we're going - set the relevant attr and remove the
        # extra item so it's not displayed
        if len(self.results) > per_page:
            if query.is_reversed:
                self.results = self.results[1:]
                self.has_prev_page = True
            else:
                self.has_next_page = True
                self.results = self.results[:-1]

        # if the query came back empty for some reason, we won't be able to have
        # next/prev pages since there are no items to base them on
        if not self.results:
            self.has_next_page = False
            self.has_prev_page = False

    def __iter__(self) -> Iterator[Any]:
        """Iterate over the results."""
        return iter(self.results)

    def __getitem__(self, index: int) -> Any:
        """Get a specific result."""
        return self.results[index]

    def __len__(self) -> int:
        """Return the number of results."""
        return len(self.results)

    @property
    def next_page_after_id36(self) -> str:
        """Return "after" ID36 that should be used to fetch the next page."""
        if not self.has_next_page:
            raise AttributeError

        next_id = inspect(self.results[-1]).identity[0]
        return id_to_id36(next_id)

    @property
    def prev_page_before_id36(self) -> str:
        """Return "before" ID36 that should be used to fetch the prev page."""
        if not self.has_prev_page:
            raise AttributeError

        prev_id = inspect(self.results[0]).identity[0]
        return id_to_id36(prev_id)


class MixedPaginatedResults(PaginatedResults):
    """Merged result from multiple PaginatedResults, consisting of different types."""

    def __init__(self, paginated_results: Sequence[PaginatedResults]):
        # pylint: disable=super-init-not-called,protected-access
        """Merge all the supplied results into a single one."""
        sort_column_name = paginated_results[0].query._sort_column.name
        if any(
            [r.query._sort_column.name != sort_column_name for r in paginated_results]
        ):
            raise ValueError("All results must by sorted by the same column.")

        reverse_sort = paginated_results[0].query.sort_desc
        if any([r.query.sort_desc != reverse_sort for r in paginated_results]):
            raise ValueError("All results must by sorted in the same direction.")

        is_query_reversed = paginated_results[0].query.is_reversed
        if any([r.query.is_reversed != is_query_reversed for r in paginated_results]):
            raise ValueError("All results must have the same directionality.")

        # merge all the results into one list and sort it
        self.results = sorted(
            chain.from_iterable(paginated_results),
            key=lambda post: getattr(post, sort_column_name),
            reverse=reverse_sort,
        )

        self.per_page = min([r.per_page for r in paginated_results])

        self.has_prev_page = any([r.has_prev_page for r in paginated_results])
        self.has_next_page = any([r.has_next_page for r in paginated_results])

        if len(self.results) > self.per_page:
            if is_query_reversed:
                self.results = self.results[-self.per_page :]
                self.has_prev_page = True
            else:
                self.results = self.results[: self.per_page]
                self.has_next_page = True

    @property
    def next_page_after_id36(self) -> str:
        """Return "after" ID36 that should be used to fetch the next page."""
        next_id36 = super().next_page_after_id36
        type_char = self.results[-1].__class__.__name__.lower()[0]

        return f"{type_char}-{next_id36}"

    @property
    def prev_page_before_id36(self) -> str:
        """Return "before" ID36 that should be used to fetch the prev page."""
        prev_id36 = super().prev_page_before_id36
        type_char = self.results[0].__class__.__name__.lower()[0]

        return f"{type_char}-{prev_id36}"
