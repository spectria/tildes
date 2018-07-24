"""Web API endpoints related to users."""

from typing import Optional

from marshmallow import ValidationError
from marshmallow.fields import String
from pyramid.httpexceptions import HTTPForbidden, HTTPUnprocessableEntity
from pyramid.request import Request
from pyramid.response import Response
from sqlalchemy.exc import IntegrityError
from webargs.pyramidparser import use_kwargs

from tildes.enums import LogEventType, TopicSortOption
from tildes.models.log import Log
from tildes.models.user import User, UserInviteCode
from tildes.schemas.fields import Enum, ShortTimePeriod
from tildes.schemas.topic import TopicSchema
from tildes.schemas.user import UserSchema
from tildes.views import IC_NOOP
from tildes.views.decorators import ic_view_config


PASSWORD_FIELD = UserSchema(only=('password',)).fields['password']


@ic_view_config(
    route_name='user',
    request_method='PATCH',
    request_param='ic-trigger-name=password-change',
    permission='change_password',
)
@use_kwargs({
    'old_password': PASSWORD_FIELD,
    'new_password': PASSWORD_FIELD,
    'new_password_confirm': PASSWORD_FIELD,
})
def change_password(
        request: Request,
        old_password: str,
        new_password: str,
        new_password_confirm: str,
) -> Response:
    """Change the logged-in user's password."""
    user = request.context

    # enable checking the new password against the breached-passwords list
    user.schema.context['check_breached_passwords'] = True

    if new_password != new_password_confirm:
        raise HTTPUnprocessableEntity(
            'New password and confirmation do not match.')

    user.change_password(old_password, new_password)

    return Response('Your password has been updated')


@ic_view_config(
    route_name='user',
    request_method='PATCH',
    request_param='ic-trigger-name=account-recovery-email',
    permission='change_email_address',
)
@use_kwargs(UserSchema(only=('email_address', 'email_address_note')))
def change_email_address(
        request: Request,
        email_address: str,
        email_address_note: str
) -> Response:
    """Change the user's email address (and descriptive note)."""
    user = request.context

    # If the user already has an email address set, we need to retain the
    # previous hash and description in the log. Otherwise, if an account is
    # compromised and the attacker changes the email address, we'd have no way
    # to support recovery for the owner.
    log_info = None
    if user.email_address_hash:
        log_info = {
            'old_hash': user.email_address_hash,
            'old_note': user.email_address_note,
        }
    request.db_session.add(Log(LogEventType.USER_EMAIL_SET, request, log_info))

    user.email_address = email_address
    user.email_address_note = email_address_note

    return Response('Your email address has been updated')


@ic_view_config(
    route_name='user',
    request_method='PATCH',
    request_param='ic-trigger-name=auto-mark-notifications-read',
    permission='change_auto_mark_notifications_read_setting',
)
def change_auto_mark_notifications(request: Request) -> Response:
    """Change the user's "automatically mark notifications read" setting."""
    user = request.context

    auto_mark = bool(request.params.get('auto_mark_notifications_read'))
    user.auto_mark_notifications_read = auto_mark

    return IC_NOOP


@ic_view_config(
    route_name='user',
    request_method='PATCH',
    request_param='ic-trigger-name=open-links-new-tab',
    permission='change_open_links_new_tab_setting',
)
def change_open_links_new_tab(request: Request) -> Response:
    """Change the user's "open links in new tabs" setting."""
    user = request.context

    external = bool(request.params.get('open_new_tab_external'))
    internal = bool(request.params.get('open_new_tab_internal'))
    text = bool(request.params.get('open_new_tab_text'))
    user.open_new_tab_external = external
    user.open_new_tab_internal = internal
    user.open_new_tab_text = text

    return IC_NOOP


@ic_view_config(
    route_name='user',
    request_method='PATCH',
    request_param='ic-trigger-name=comment-visits',
    permission='change_comment_visits_setting',
)
def change_track_comment_visits(request: Request) -> Response:
    """Change the user's "track comment visits" setting."""
    user = request.context

    track_comment_visits = bool(request.params.get('track_comment_visits'))
    user.track_comment_visits = track_comment_visits

    if track_comment_visits:
        return Response("Enabled tracking of last comment visit.")

    return Response("Disabled tracking of last comment visit.")


@ic_view_config(
    route_name='user_invite_code',
    request_method='GET',
    permission='view_invite_code',
    renderer='invite_code.jinja2',
)
def get_invite_code(request: Request) -> dict:
    """Generate a new invite code owned by the user."""
    user = request.context

    if request.user.invite_codes_remaining < 1:
        raise HTTPForbidden('No invite codes remaining')

    # obtain a lock to prevent concurrent requests generating multiple codes
    request.obtain_lock('generate_invite_code', user.user_id)

    # it's possible to randomly generate an existing code, so we'll retry
    # until we create a new one (will practically always be the first try)
    while True:
        savepoint = request.tm.savepoint()

        code = UserInviteCode(user)
        request.db_session.add(code)

        try:
            request.db_session.flush()
            break
        except IntegrityError:
            savepoint.rollback()

    # doing an atomic decrement on request.user.invite_codes_remaining is going
    # to make it unusable as an integer in the template, so store the expected
    # value after the decrement first, to be able to use that instead
    num_remaining = request.user.invite_codes_remaining - 1
    request.user.invite_codes_remaining = User.invite_codes_remaining - 1

    return {'code': code, 'num_remaining': num_remaining}


@ic_view_config(
    route_name='user_default_listing_options',
    request_method='PUT',
    permission='edit_default_listing_options',
)
@use_kwargs({
    'order': Enum(TopicSortOption),
    'period': ShortTimePeriod(allow_none=True),
})
def put_default_listing_options(
        request: Request,
        order: TopicSortOption,
        period: Optional[ShortTimePeriod],
) -> dict:
    """Set the user's default listing options."""
    user = request.context

    user.home_default_order = order
    if period:
        user.home_default_period = period.as_short_form()
    else:
        user.home_default_period = 'all'

    return IC_NOOP


@ic_view_config(
    route_name='user_filtered_topic_tags',
    request_method='PUT',
    permission='edit_filtered_topic_tags',
)
@use_kwargs({'tags': String()})
def put_filtered_topic_tags(request: Request, tags: str) -> dict:
    """Update a user's filtered topic tags list."""
    if not tags:
        request.user.filtered_topic_tags = []
        return IC_NOOP

    split_tags = tags.split(',')

    try:
        schema = TopicSchema(only=('tags',))
        result = schema.load({'tags': split_tags})
    except ValidationError:
        raise ValidationError({'tags': ['Invalid tags']})

    request.user.filtered_topic_tags = result.data['tags']

    return IC_NOOP
