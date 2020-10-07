"""Views relating to ignored topics."""

from typing import Optional

from pyramid.request import Request
from pyramid.view import view_config
from sqlalchemy.sql import desc

from tildes.models.topic import Topic, TopicIgnore
from tildes.schemas.listing import PaginatedListingSchema
from tildes.views.decorators import use_kwargs


@view_config(route_name="ignored_topics", renderer="ignored_topics.jinja2")
@use_kwargs(PaginatedListingSchema())
def get_ignored_topics(
    request: Request,
    after: Optional[str],
    before: Optional[str],
    per_page: int,
) -> dict:
    """Generate the ignored topics page."""
    # pylint: disable=unused-argument
    user = request.user

    query = request.query(Topic).only_ignored().order_by(desc(TopicIgnore.created_time))

    if before:
        query = query.before_id36(before)

    if after:
        query = query.after_id36(after)

    query = query.join_all_relationships()

    topics = query.all()

    return {"user": user, "topics": topics}
