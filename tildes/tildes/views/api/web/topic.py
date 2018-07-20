"""Web API endpoints related to topics."""

from marshmallow import ValidationError
from marshmallow.fields import String
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from pyramid.request import Request
from sqlalchemy.exc import IntegrityError
from webargs.pyramidparser import use_kwargs

from tildes.enums import LogEventType
from tildes.models.group import Group
from tildes.models.log import LogTopic
from tildes.models.topic import Topic, TopicVote
from tildes.schemas.group import GroupSchema
from tildes.schemas.topic import TopicSchema
from tildes.views import IC_NOOP
from tildes.views.decorators import ic_view_config


@ic_view_config(
    route_name='topic',
    request_method='GET',
    request_param='ic-trigger-name=edit',
    renderer='topic_edit.jinja2',
    permission='edit',
)
def get_topic_edit(request: Request) -> dict:
    """Get the edit form for a topic with Intercooler."""
    return {'topic': request.context}


@ic_view_config(
    route_name='topic',
    request_method='GET',
    renderer='topic_contents.jinja2',
    permission='view',
)
def get_topic_contents(request: Request) -> dict:
    """Get a topic's body with Intercooler."""
    return {'topic': request.context}


@ic_view_config(
    route_name='topic',
    request_method='PATCH',
    renderer='topic_contents.jinja2',
    permission='edit',
)
@use_kwargs(TopicSchema(only=('markdown',)))
def patch_topic(request: Request, markdown: str) -> dict:
    """Update a topic with Intercooler."""
    topic = request.context

    topic.markdown = markdown

    return {'topic': topic}


@ic_view_config(
    route_name='topic',
    request_method='DELETE',
    permission='delete',
)
def delete_topic(request: Request) -> Response:
    """Delete a topic with Intercooler and redirect to its group."""
    topic = request.context
    topic.is_deleted = True

    response = Response()
    response.headers['X-IC-Redirect'] = request.route_url(
        'group', group_path=topic.group.path)

    return response


@ic_view_config(
    route_name='topic_vote',
    request_method='PUT',
    renderer='topic_voting.jinja2',
    permission='vote',
)
def vote_topic(request: Request) -> Response:
    """Vote on a topic with Intercooler."""
    topic = request.context

    savepoint = request.tm.savepoint()

    new_vote = TopicVote(request.user, topic)
    request.db_session.add(new_vote)

    try:
        # manually flush before attempting to commit, to avoid having all
        # objects detached from the session in case of an error
        request.db_session.flush()
        request.tm.commit()
    except IntegrityError:
        # the user has already voted on this topic
        savepoint.rollback()

    # re-query the topic to get complete data
    topic = (
        request.query(Topic)
        .join_all_relationships()
        .filter_by(topic_id=topic.topic_id)
        .one()
    )

    return {'topic': topic}


@ic_view_config(
    route_name='topic_vote',
    request_method='DELETE',
    renderer='topic_voting.jinja2',
    permission='vote',
)
def unvote_topic(request: Request) -> Response:
    """Remove the user's vote from a topic with Intercooler."""
    topic = request.context

    request.query(TopicVote).filter(
        TopicVote.topic == topic,
        TopicVote.user == request.user,
    ).delete(synchronize_session=False)

    # manually commit the transaction so triggers will execute
    request.tm.commit()

    # re-query the topic to get complete data
    topic = (
        request.query(Topic)
        .join_all_relationships()
        .filter_by(topic_id=topic.topic_id)
        .one()
    )

    return {'topic': topic}


@ic_view_config(
    route_name='topic_tags',
    request_method='GET',
    renderer='topic_tags_edit.jinja2',
    permission='tag',
)
def get_topic_tags(request: Request) -> dict:
    """Get the tagging form for a topic with Intercooler."""
    return {'topic': request.context}


@ic_view_config(
    route_name='topic_tags',
    request_method='PUT',
    renderer='topic_tags.jinja2',
    permission='tag',
)
@use_kwargs({'tags': String()})
def tag_topic(request: Request, tags: str) -> dict:
    """Apply tags to a topic with Intercooler."""
    topic = request.context

    if tags:
        # split the tag string on commas
        new_tags = tags.split(',')
    else:
        new_tags = []

    old_tags = topic.tags

    try:
        topic.tags = new_tags
    except ValidationError:
        raise ValidationError({'tags': ['Invalid tags']})

    # if tags weren't changed, don't add a log entry or update page
    if set(topic.tags) == set(old_tags):
        return IC_NOOP

    request.db_session.add(
        LogTopic(
            LogEventType.TOPIC_TAG,
            request,
            topic,
            info={'old': old_tags, 'new': topic.tags},
        ),
    )

    return {'topic': topic}


@ic_view_config(
    route_name='topic_group',
    request_method='GET',
    renderer='topic_group_edit.jinja2',
    permission='move',
)
def get_topic_group(request: Request) -> dict:
    """Get the form for moving a topic with Intercooler."""
    return {'topic': request.context}


@ic_view_config(
    route_name='topic',
    request_param='ic-trigger-name=topic-move',
    request_method='PATCH',
    permission='move',
)
@use_kwargs(GroupSchema(only=('path',)))
def move_topic(request: Request, path: str) -> dict:
    """Move a topic to a different group with Intercooler."""
    topic = request.context

    new_group = (
        request.query(Group)
        .filter(Group.path == path)
        .one_or_none()
    )
    if not new_group:
        raise HTTPNotFound('Group not found')

    old_group = topic.group

    if new_group == old_group:
        return IC_NOOP

    topic.group = new_group

    request.db_session.add(
        LogTopic(
            LogEventType.TOPIC_MOVE,
            request,
            topic,
            info={'old': str(old_group.path), 'new': str(topic.group.path)}
        ),
    )

    return Response('Moved')


@ic_view_config(
    route_name='topic_lock',
    request_method='PUT',
    permission='lock',
)
def lock_topic(request: Request) -> Response:
    """Lock a topic with Intercooler."""
    topic = request.context

    topic.is_locked = True
    request.db_session.add(LogTopic(LogEventType.TOPIC_LOCK, request, topic))

    return Response('Locked')


@ic_view_config(
    route_name='topic_lock',
    request_method='DELETE',
    permission='lock',
)
def unlock_topic(request: Request) -> Response:
    """Unlock a topic with Intercooler."""
    topic = request.context

    topic.is_locked = False
    request.db_session.add(LogTopic(LogEventType.TOPIC_UNLOCK, request, topic))

    return Response('Unlocked')


@ic_view_config(
    route_name='topic_title',
    request_method='GET',
    renderer='topic_title_edit.jinja2',
    permission='edit_title',
)
def get_topic_title(request: Request) -> dict:
    """Get the form for editing a topic's title with Intercooler."""
    return {'topic': request.context}


@ic_view_config(
    route_name='topic',
    request_param='ic-trigger-name=topic-title-edit',
    request_method='PATCH',
    permission='edit_title',
)
@use_kwargs(TopicSchema(only=('title',)))
def edit_topic_title(request: Request, title: str) -> dict:
    """Edit a topic's title with Intercooler."""
    topic = request.context

    if title == topic.title:
        return IC_NOOP

    request.db_session.add(
        LogTopic(
            LogEventType.TOPIC_TITLE_EDIT,
            request,
            topic,
            info={'old': topic.title, 'new': title}
        ),
    )

    topic.title = title

    return Response(topic.title)
