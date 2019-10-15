# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views related to user settings."""

from datetime import timedelta
from io import BytesIO
import sys

import pyotp
import qrcode
from pyramid.httpexceptions import HTTPForbidden, HTTPUnprocessableEntity
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_config
from sqlalchemy import func
from webargs.pyramidparser import use_kwargs

from tildes.enums import CommentLabelOption, CommentTreeSortOption
from tildes.lib.datetime import utc_now
from tildes.lib.string import separate_string
from tildes.models.comment import Comment, CommentLabel, CommentTree
from tildes.models.group import Group
from tildes.models.topic import Topic
from tildes.models.user import User
from tildes.schemas.user import (
    BIO_MAX_LENGTH,
    EMAIL_ADDRESS_NOTE_MAX_LENGTH,
    UserSchema,
)


PASSWORD_FIELD = UserSchema(only=("password",)).fields["password"]

THEME_OPTIONS = {
    "white": "White",
    "solarized-light": "Solarized Light",
    "solarized-dark": "Solarized Dark",
    "dracula": "Dracula",
    "atom-one-dark": "Atom One Dark",
    "black": "Black",
    "zenburn": "Zenburn",
    "gruvbox-light": "Gruvbox Light",
    "gruvbox-dark": "Gruvbox Dark",
}


@view_config(route_name="settings", renderer="settings.jinja2")
def get_settings(request: Request) -> dict:
    """Generate the user settings page."""
    site_default_theme = "white"
    user_default_theme = request.user.theme_default or site_default_theme

    current_theme = request.cookies.get("theme", "") or user_default_theme

    # Make a copy of the theme options dict so we can add info to the names
    theme_options = THEME_OPTIONS.copy()

    if site_default_theme == user_default_theme:
        theme_options[site_default_theme] += " (site and account default)"
    else:
        theme_options[user_default_theme] += " (account default)"
        theme_options[site_default_theme] += " (site default)"

    return {"current_theme": current_theme, "theme_options": theme_options}


@view_config(
    route_name="settings_account_recovery", renderer="settings_account_recovery.jinja2"
)
def get_settings_account_recovery(request: Request) -> dict:
    """Generate the account recovery page."""
    # pylint: disable=unused-argument
    return {"note_max_length": EMAIL_ADDRESS_NOTE_MAX_LENGTH}


@view_config(route_name="settings_two_factor", renderer="settings_two_factor.jinja2")
def get_settings_two_factor(request: Request) -> dict:
    """Generate the two-factor authentication page."""
    # Generate a new secret key if the user doesn't have one.
    if request.user.two_factor_secret is None:
        request.user.two_factor_secret = pyotp.random_base32()

    return {
        "two_factor_secret": separate_string(request.user.two_factor_secret, " ", 4)
    }


@view_config(
    route_name="settings_comment_visits", renderer="settings_comment_visits.jinja2"
)
def get_settings_comment_visits(request: Request) -> dict:
    """Generate the comment visits settings page."""
    # pylint: disable=unused-argument
    return {}


@view_config(route_name="settings_filters", renderer="settings_filters.jinja2")
def get_settings_filters(request: Request) -> dict:
    """Generate the filters settings page."""
    # pylint: disable=unused-argument
    return {}


@view_config(
    route_name="settings_password_change", renderer="settings_password_change.jinja2"
)
def get_settings_password_change(request: Request) -> dict:
    """Generate the password change page."""
    # pylint: disable=unused-argument
    return {}


@view_config(route_name="settings_two_factor_qr_code")
def get_settings_two_factor_qr_code(request: Request) -> Response:
    """Generate the 2FA QR code."""
    # If 2FA is already enabled, don't expose the secret.
    if request.user.two_factor_enabled:
        raise HTTPForbidden("Already enabled")

    totp = pyotp.totp.TOTP(request.user.two_factor_secret)
    otp_uri = totp.provisioning_uri(request.user.username, issuer_name="Tildes")
    byte_io = BytesIO()
    img = qrcode.make(otp_uri, border=2, box_size=4)

    img.save(byte_io, "PNG")

    return Response(byte_io.getvalue(), cache_control="private, no-cache")


@view_config(route_name="settings_bio", renderer="settings_bio.jinja2")
def get_settings_bio(request: Request) -> dict:
    """Generate the user bio settings page."""
    # pylint: disable=unused-argument
    return {"bio_max_length": BIO_MAX_LENGTH}


@view_config(route_name="settings_password_change", request_method="POST")
@use_kwargs(
    {
        "old_password": PASSWORD_FIELD,
        "new_password": PASSWORD_FIELD,
        "new_password_confirm": PASSWORD_FIELD,
    }
)
def post_settings_password_change(
    request: Request, old_password: str, new_password: str, new_password_confirm: str
) -> Response:
    """Change the logged-in user's password."""
    # enable checking the new password against the breached-passwords list
    request.user.schema.context["check_breached_passwords"] = True

    if new_password != new_password_confirm:
        raise HTTPUnprocessableEntity("New password and confirmation do not match.")

    request.user.change_password(old_password, new_password)

    return Response("Your password has been updated")


@view_config(
    route_name="settings_theme_previews", renderer="settings_theme_previews.jinja2"
)
def get_settings_theme_previews(request: Request) -> dict:
    """Generate the theme preview page."""
    # get the generic/unknown user and a random group to display on the example posts
    fake_user = request.query(User).filter(User.user_id == -1).one()
    group = request.query(Group).order_by(func.random()).limit(1).one()

    fake_link_topic = Topic.create_link_topic(
        group, fake_user, "Example Link Topic", "https://tildes.net/"
    )

    fake_text_topic = Topic.create_text_topic(
        group, fake_user, "Example Text Topic", "No real text"
    )
    fake_text_topic.content_metadata = {
        "excerpt": "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    }

    fake_topics = [fake_link_topic, fake_text_topic]

    # manually add other necessary attributes to the fake topics
    for fake_topic in fake_topics:
        fake_topic.topic_id = sys.maxsize
        fake_topic.tags = ["tag one", "tag two"]
        fake_topic.num_comments = 123
        fake_topic.num_votes = 12
        fake_topic.created_time = utc_now() - timedelta(hours=12)

    # create a fake top-level comment that appears to be written by the user
    markdown = (
        "This is what a regular comment written by yourself would look like.\n\n"
        "It has **formatting** and a [link](https://tildes.net)."
    )
    fake_top_comment = Comment(fake_link_topic, request.user, markdown)
    fake_top_comment.comment_id = sys.maxsize
    fake_top_comment.created_time = utc_now() - timedelta(hours=12, minutes=30)

    child_comments_markdown = [
        (
            "This reply has received an Exemplary label. It also has a blockquote:\n\n"
            "> Hello World!"
        ),
        (
            "This is a reply written by the topic's OP with a code block in it:\n\n"
            "```js\n"
            "function foo() {\n"
            "    ['1', '2', '3'].map(parseInt);\n"
            "}\n"
            "```"
        ),
        (
            "This reply is new and has the *Mark New Comments* stripe on its left "
            "(even if you don't have that feature enabled)."
        ),
    ]

    fake_comments = [fake_top_comment]

    # vary the ID and created_time on each fake comment so CommentTree works properly
    current_comment_id = fake_top_comment.comment_id
    current_created_time = fake_top_comment.created_time
    for markdown in child_comments_markdown:
        current_comment_id -= 1
        current_created_time += timedelta(minutes=5)

        fake_comment = Comment(
            fake_link_topic, fake_user, markdown, parent_comment=fake_top_comment
        )
        fake_comment.comment_id = current_comment_id
        fake_comment.created_time = current_created_time
        fake_comment.parent_comment_id = fake_top_comment.comment_id

        fake_comments.append(fake_comment)

    # add other necessary attributes to all of the fake comments
    for fake_comment in fake_comments:
        fake_comment.num_votes = 0

    fake_tree = CommentTree(
        fake_comments, CommentTreeSortOption.RELEVANCE, request.user
    )

    # add a fake Exemplary label to the first child comment
    fake_comments[1].labels = [
        CommentLabel(fake_comments[1], fake_user, CommentLabelOption.EXEMPLARY, 1.0)
    ]

    # the comment to mark as new is the last one, so set a visit time just before it
    fake_last_visit_time = fake_comments[-1].created_time - timedelta(minutes=1)

    return {
        "theme_options": THEME_OPTIONS,
        "fake_topics": fake_topics,
        "fake_comment_tree": fake_tree,
        "last_visit": fake_last_visit_time,
    }
