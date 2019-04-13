# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Web API endpoints related to users."""

import random
import string
from typing import Optional

from marshmallow import ValidationError
from marshmallow.fields import String
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPUnauthorized,
    HTTPUnprocessableEntity,
)
from pyramid.request import Request
from pyramid.response import Response
from sqlalchemy.exc import IntegrityError
from webargs.pyramidparser import use_kwargs

from tildes.enums import LogEventType, TopicSortOption
from tildes.lib.string import separate_string
from tildes.models.log import Log
from tildes.models.user import User, UserInviteCode
from tildes.schemas.fields import Enum, ShortTimePeriod
from tildes.schemas.topic import TopicSchema
from tildes.schemas.user import UserSchema
from tildes.views import IC_NOOP
from tildes.views.decorators import ic_view_config


PASSWORD_FIELD = UserSchema(only=("password",)).fields["password"]


@ic_view_config(
    route_name="user",
    request_method="PATCH",
    request_param="ic-trigger-name=password-change",
    permission="change_password",
)
@use_kwargs(
    {
        "old_password": PASSWORD_FIELD,
        "new_password": PASSWORD_FIELD,
        "new_password_confirm": PASSWORD_FIELD,
    }
)
def patch_change_password(
    request: Request, old_password: str, new_password: str, new_password_confirm: str
) -> Response:
    """Change the logged-in user's password."""
    user = request.context

    # enable checking the new password against the breached-passwords list
    user.schema.context["check_breached_passwords"] = True

    if new_password != new_password_confirm:
        raise HTTPUnprocessableEntity("New password and confirmation do not match.")

    user.change_password(old_password, new_password)

    return Response("Your password has been updated")


@ic_view_config(
    route_name="user",
    request_method="PATCH",
    request_param="ic-trigger-name=account-recovery-email",
    permission="change_email_address",
)
@use_kwargs(UserSchema(only=("email_address", "email_address_note")))
def patch_change_email_address(
    request: Request, email_address: str, email_address_note: str
) -> Response:
    """Change the user's email address (and descriptive note)."""
    user = request.context

    # If the user already has an email address set, we need to retain the previous hash
    # and description in the log. Otherwise, if an account is compromised and the
    # attacker changes the email address, we'd have no way to support recovery for the
    # owner.
    log_info = None
    if user.email_address_hash:
        log_info = {
            "old_hash": user.email_address_hash,
            "old_note": user.email_address_note,
        }
    request.db_session.add(Log(LogEventType.USER_EMAIL_SET, request, log_info))

    user.email_address = email_address
    user.email_address_note = email_address_note

    return Response("Your email address has been updated")


@ic_view_config(
    route_name="user",
    request_method="POST",
    request_param="ic-trigger-name=enable-two-factor",
    renderer="two_factor_enabled.jinja2",
    permission="change_two_factor",
)
@use_kwargs({"code": String()})
def post_enable_two_factor(request: Request, code: str) -> dict:
    """Enable two-factor authentication for the user."""
    user = request.context

    if not user.is_correct_two_factor_code(code):
        raise HTTPUnprocessableEntity("Invalid code, please try again.")

    request.user.two_factor_enabled = True

    # Generate 10 backup codes (16 lowercase letters each)
    request.user.two_factor_backup_codes = [
        "".join(random.choices(string.ascii_lowercase, k=16)) for _ in range(10)
    ]

    # format the backup codes to be easier to read for output
    backup_codes = [
        separate_string(code, " ", 4) for code in request.user.two_factor_backup_codes
    ]

    return {"backup_codes": backup_codes}


@ic_view_config(
    route_name="user",
    request_method="POST",
    request_param="ic-trigger-name=disable-two-factor",
    renderer="two_factor_disabled.jinja2",
    permission="change_two_factor",
)
@use_kwargs({"code": String()})
def post_disable_two_factor(request: Request, code: str) -> Response:
    """Disable two-factor authentication for the user."""
    if not request.user.is_correct_two_factor_code(code):
        raise HTTPUnauthorized(body="Invalid code")

    request.user.two_factor_enabled = False
    request.user.two_factor_secret = None
    request.user.two_factor_backup_codes = None

    return {}


@ic_view_config(
    route_name="user",
    request_method="PATCH",
    request_param="ic-trigger-name=auto-mark-notifications-read",
    permission="change_auto_mark_notifications_read_setting",
)
def patch_change_auto_mark_notifications(request: Request) -> Response:
    """Change the user's "automatically mark notifications read" setting."""
    user = request.context

    auto_mark = bool(request.params.get("auto_mark_notifications_read"))
    user.auto_mark_notifications_read = auto_mark

    return IC_NOOP


@ic_view_config(
    route_name="user",
    request_method="PATCH",
    request_param="ic-trigger-name=interact-mark-notifications-read",
    permission="change_interact_mark_notifications_read_setting",
)
def patch_change_interact_mark_notifications(request: Request) -> Response:
    """Change the user's "automatically mark notifications read on interact" setting."""
    user = request.context

    new_value = bool(request.params.get("interact_mark_notifications_read"))
    user.interact_mark_notifications_read = new_value

    return IC_NOOP


@ic_view_config(
    route_name="user",
    request_method="PATCH",
    request_param="ic-trigger-name=open-links-new-tab",
    permission="change_open_links_new_tab_setting",
)
def patch_change_open_links_new_tab(request: Request) -> Response:
    """Change the user's "open links in new tabs" setting."""
    user = request.context

    external = bool(request.params.get("open_new_tab_external"))
    internal = bool(request.params.get("open_new_tab_internal"))
    text = bool(request.params.get("open_new_tab_text"))
    user.open_new_tab_external = external
    user.open_new_tab_internal = internal
    user.open_new_tab_text = text

    return IC_NOOP


@ic_view_config(
    route_name="user",
    request_method="PATCH",
    request_param="ic-trigger-name=comment-visits",
    permission="change_comment_visits_setting",
)
def patch_change_track_comment_visits(request: Request) -> Response:
    """Change the user's "track comment visits" setting."""
    user = request.context

    track_comment_visits = bool(request.params.get("track_comment_visits"))
    user.track_comment_visits = track_comment_visits

    return IC_NOOP


@ic_view_config(
    route_name="user",
    request_method="PATCH",
    request_param="ic-trigger-name=collapse-old-comments",
    permission="change_collapse_old_comments_setting",
)
def patch_change_collapse_old_comments(request: Request) -> Response:
    """Change the user's "collapse old comments" setting."""
    user = request.context

    collapse_old_comments = bool(request.params.get("collapse_old_comments"))
    user.collapse_old_comments = collapse_old_comments

    return IC_NOOP


@ic_view_config(
    route_name="user",
    request_method="PATCH",
    request_param="ic-trigger-name=account-default-theme",
    permission="change_account_default_theme_setting",
)
def patch_change_account_default_theme(request: Request) -> Response:
    """Change the user's "theme account default" setting."""
    user = request.context

    new_theme = request.params.get("theme")
    user.theme_default = new_theme

    return IC_NOOP


@ic_view_config(
    route_name="user",
    request_method="PATCH",
    request_param="ic-trigger-name=user-bio",
    permission="edit_bio",
)
@use_kwargs({"markdown": String()})
def patch_change_user_bio(request: Request, markdown: str) -> dict:
    """Update a user's bio."""
    user = request.context

    user.bio_markdown = markdown

    return IC_NOOP


@ic_view_config(
    route_name="user_invite_code",
    request_method="GET",
    permission="view_invite_code",
    renderer="invite_code.jinja2",
)
def get_invite_code(request: Request) -> dict:
    """Generate a new invite code owned by the user."""
    user = request.context

    if request.user.invite_codes_remaining < 1:
        raise HTTPForbidden("No invite codes remaining")

    # obtain a lock to prevent concurrent requests generating multiple codes
    request.obtain_lock("generate_invite_code", user.user_id)

    # it's possible to randomly generate an existing code, so we'll retry until we
    # create a new one (will practically always be the first try)
    while True:
        savepoint = request.tm.savepoint()

        code = UserInviteCode(user)
        request.db_session.add(code)

        try:
            request.db_session.flush()
            break
        except IntegrityError:
            savepoint.rollback()

    # doing an atomic decrement on request.user.invite_codes_remaining is going to make
    # it unusable as an integer in the template, so store the expected value after the
    # decrement first, to be able to use that instead
    num_remaining = request.user.invite_codes_remaining - 1
    request.user.invite_codes_remaining = User.invite_codes_remaining - 1

    return {"code": code, "num_remaining": num_remaining}


@ic_view_config(
    route_name="user_default_listing_options",
    request_method="PUT",
    permission="edit_default_listing_options",
)
@use_kwargs(
    {"order": Enum(TopicSortOption), "period": ShortTimePeriod(allow_none=True)}
)
def put_default_listing_options(
    request: Request, order: TopicSortOption, period: Optional[ShortTimePeriod]
) -> dict:
    """Set the user's default listing options."""
    user = request.context

    user.home_default_order = order
    if period:
        user.home_default_period = period.as_short_form()
    else:
        user.home_default_period = "all"

    return IC_NOOP


@ic_view_config(
    route_name="user_filtered_topic_tags",
    request_method="PUT",
    permission="edit_filtered_topic_tags",
)
@use_kwargs({"tags": String()})
def put_filtered_topic_tags(request: Request, tags: str) -> dict:
    """Update a user's filtered topic tags list."""
    if not tags or tags.isspace():
        request.user.filtered_topic_tags = []
        return IC_NOOP

    split_tags = tags.replace("\r", "").split("\n")

    try:
        schema = TopicSchema(only=("tags",))
        result = schema.load({"tags": split_tags})
    except ValidationError:
        raise ValidationError({"tags": ["Invalid tags"]})

    request.user.filtered_topic_tags = result.data["tags"]

    return IC_NOOP


@ic_view_config(route_name="user_ban", request_method="PUT", permission="ban")
def put_user_ban(request: Request) -> Response:
    """Ban a user."""
    user = request.context

    user.is_banned = True

    # delete all of the user's outstanding invite codes
    request.query(UserInviteCode).filter(
        UserInviteCode.user_id == user.user_id,
        UserInviteCode.invitee_id == None,  # noqa
    ).delete(synchronize_session=False)

    return Response("Banned")


@ic_view_config(route_name="user_ban", request_method="DELETE", permission="ban")
def delete_user_ban(request: Request) -> Response:
    """Unban a user."""
    request.context.is_banned = False

    return Response("Unbanned")
