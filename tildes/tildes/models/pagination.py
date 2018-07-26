"""Contains the PaginatedQuery and PaginatedResults classes."""

from typing import Any, Iterator, List, Optional, TypeVar

from pyramid.request import Request
from sqlalchemy import Column, func

from tildes.lib.id import id36_to_id
from .model_query import ModelQuery


ModelType = TypeVar('ModelType')  # pylint: disable=invalid-name


class PaginatedQuery(ModelQuery):
    """ModelQuery subclass that supports being split into pages."""

    def __init__(self, model_cls: Any, request: Request) -> None:
        """Initialize a PaginatedQuery for the specified model and request."""
        if len(model_cls.__table__.primary_key) > 1:
            raise TypeError('Only single-col primary key tables are supported')

        super().__init__(model_cls, request)

        self._sort_column: Optional[Column] = None
        self.sort_desc = True

        self.after_id: Optional[int] = None
        self.before_id: Optional[int] = None

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

        # always add a final sort by the ID so keyset pagination works properly
        return [self._sort_column] + list(self.model_cls.__table__.primary_key)

    @property
    def sorting_columns_desc(self) -> List[Column]:
        """Return descending versions of the sorting columns."""
        return [col.desc() for col in self.sorting_columns]

    @property
    def is_reversed(self) -> bool:
        """Return whether the query is operating "in reverse".

        This is a bit confusing. When moving "forward" through pages, items
        will be queried in the same order that they are displayed. For example,
        when displaying the newest topics, the query is simply for "newest N
        topics" (where N is the number of items per page), with an optional
        "after topic X" clause. Either way, the first result from the query
        will have the highest created_time, and should be the first item
        displayed.

        However, things work differently when you are paging "backwards". Since
        this is done by looking before a specific item, the query needs to
        fetch items in the opposite order of how they will be displayed. For
        the "newest" sort example, when paging backwards you need to query for
        "*oldest* N items before topic X", so the query ordering is the exact
        opposite of the desired display order. The first result from the query
        will have the *lowest* created_time, so should be the last item
        displayed. Because of this, the results need to be reversed.
        """
        return bool(self.before_id)

    def after_id36(self, id36: str) -> 'PaginatedQuery':
        """Restrict the query to results after an id36 (generative)."""
        if self.before_id:
            raise ValueError("Can't set both before and after restrictions")

        self.after_id = id36_to_id(id36)

        return self

    def before_id36(self, id36: str) -> 'PaginatedQuery':
        """Restrict the query to results before an id36 (generative)."""
        if self.after_id:
            raise ValueError("Can't set both before and after restrictions")

        self.before_id = id36_to_id(id36)

        return self

    def _apply_before_or_after(self) -> 'PaginatedQuery':
        """Apply the "before" or "after" restrictions if necessary."""
        if not (self.after_id or self.before_id):
            return self

        query = self

        # determine the ID of the "anchor item" that we're using as an upper or
        # lower bound, and which type of bound it is
        if self.after_id:
            anchor_id = self.after_id

            # since we're looking for other items "after" the anchor item, it
            # will act as an upper bound when the sort order is descending,
            # otherwise it's a lower bound
            is_anchor_upper_bound = self.sort_desc
        elif self.before_id:
            anchor_id = self.before_id

            # opposite of "after" behavior - when looking "before" the anchor
            # item, it's an upper bound if the sort order is *ascending*
            is_anchor_upper_bound = not self.sort_desc

        # create a subquery to get comparison values for the anchor item
        id_column = list(self.model_cls.__table__.primary_key)[0]
        subquery = (
            self.request.db_session.query(*self.sorting_columns)
            .filter(id_column == anchor_id)
            .subquery()
        )

        # restrict the results to items on the right "side" of the anchor item
        if is_anchor_upper_bound:
            query = query.filter(func.row(*self.sorting_columns) < subquery)
        else:
            query = query.filter(func.row(*self.sorting_columns) > subquery)

        return query

    def _finalize(self) -> 'PaginatedQuery':
        """Finalize the query before execution."""
        query = super()._finalize()

        if self._sort_column:
            # if the query is reversed, we need to sort in the opposite dir
            # (basically self.sort_desc XOR self.is_reversed)
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

    def get_page(self, per_page: int) -> 'PaginatedResults':
        """Get a page worth of results from the query (`per page` items)."""
        return PaginatedResults(self, per_page)


class PaginatedResults:
    """Results from a PaginatedQuery.

    Has a few extra attributes that give info about the pagination.
    """

    def __init__(self, query: PaginatedQuery, per_page: int) -> None:
        """Fetch results from a PaginatedQuery."""
        self.per_page = per_page

        # if the query had `before` or `after` restrictions, there must be a
        # page in that direction (it's where we came from)
        self.has_next_page = bool(query.before_id)
        self.has_prev_page = bool(query.after_id)

        # fetch the results - try to get one more than we're actually going to
        # display, so that we know if there's another page
        self.results = query.limit(per_page + 1).all()

        # if we managed to get one more item than the page size, there's
        # another page in the same direction that we're going - set the
        # relevant attr and remove the extra item so it's not displayed
        if len(self.results) > per_page:
            if query.is_reversed:
                self.results = self.results[1:]
                self.has_prev_page = True
            else:
                self.has_next_page = True
                self.results = self.results[:-1]

        # if the query came back empty for some reason, we won't be able to
        # have next/prev pages since there are no items to base them on
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
