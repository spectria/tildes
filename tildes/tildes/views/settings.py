# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views related to user settings."""

from io import BytesIO
from typing import List, Optional

import pyotp
import qrcode
from pyramid.httpexceptions import HTTPForbidden, HTTPUnprocessableEntity
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_config
from webargs.pyramidparser import use_kwargs

from tildes.enums import CommentLabelOption, CommentTreeSortOption
from tildes.lib.string import separate_string
from tildes.lib.datetime import utc_from_timestamp, utc_now
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


@view_config(route_name="settings", renderer="settings.jinja2")
def get_settings(request: Request) -> dict:
    """Generate the user settings page."""
    return generate_theme_chooser_dict(request)


def generate_theme_chooser_dict(request: Request) -> dict:
    """Generate the partial response dict necessary for the settings theme selector."""
    site_default_theme = "white"
    user_default_theme = request.user.theme_default or site_default_theme

    current_theme = request.cookies.get("theme", "") or user_default_theme

    theme_options = {
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
    """Generate the theme preview page.

    On the site, the following data must not point to real data users could
    inadvertently affect with the demo widgets:
    - The user @Tildes
    - The group ~groupname
    - Topic ID 42_000_000_000
    - Comment IDs 42_000_000_000 through 42_000_000_003
    """

    fake_old_timestamp = utc_from_timestamp(int(utc_now().timestamp() - 60 * 60 * 24))
    fake_last_visit_timestamp = utc_from_timestamp(
        int(utc_now().timestamp() - 60 * 60 * 12)
    )

    fake_user = User("Tildes", "a_very_safe_password")
    fake_user.user_id = 0
    fake_user_not_op = User("Tildes", "another_very_safe_password")
    fake_user_not_op.user_id = -1
    fake_group = Group("groupname")
    fake_group.is_user_treated_as_topic_source = False

    fake_topics: List[Topic] = [
        Topic.create_link_topic(
            fake_group, fake_user, "Example Link Topic", "https://tildes.net/"
        ),
        Topic.create_text_topic(
            fake_group, fake_user, "Example Text Topic", "empty string"
        ),
    ]

    for fake_topic in fake_topics:
        fake_topic.topic_id = 42_000_000_000
        fake_topic.tags = ["a tag", "another tag"]
        fake_topic.created_time = utc_now()
        fake_topic.group = fake_group
        fake_topic.num_comments = 0
        fake_topic.num_votes = 0
        fake_topic.content_metadata = {
            "excerpt": """Lorem ipsum dolor sit amet,
            consectetur adipiscing elit. Nunc auctor purus at diam tempor,
            id viverra nunc vulputate.""",
            "word_count": 42,
        }

    def make_comment(
        markdown: str, comment_id: int, parent_id: Optional[int], is_op: bool
    ) -> Comment:
        """Create a fake comment with enough data to make the template render fine."""
        fake_comment = Comment(fake_topics[0], fake_user_not_op, markdown)
        fake_comment.comment_id = comment_id
        if parent_id:
            fake_comment.parent_comment_id = parent_id
        fake_comment.created_time = fake_old_timestamp
        fake_comment.num_votes = 0
        if is_op:
            fake_comment.user = fake_user
        return fake_comment

    fake_comments: List[Comment] = []

    fake_comments.append(
        make_comment(
            """This is a regular comment, written by yourself. \
            It has **formatting** and a [link](https://tildes.net).""",
            42_000_000_000,
            None,
            False,
        )
    )
    fake_comments[-1].user = request.user
    fake_comments.append(
        make_comment(
            """This is a reply written by the topic's OP. \
            It's new and has the *Mark New Comments* stripe on its left, \
            even if you didn't enable that feature.""",
            42_000_000_001,
            42_000_000_000,
            True,
        )
    )
    fake_comments[-1].created_time = utc_now()
    fake_comments.append(
        make_comment(
            """This reply is Exemplary. It also has a blockquote:\
            \n> Hello World!""",
            42_000_000_002,
            42_000_000_000,
            False,
        )
    )
    fake_comments[-1].labels.append(
        CommentLabel(fake_comments[-1], fake_user, CommentLabelOption.EXEMPLARY, 1.0)
    )
    fake_comments.append(
        make_comment(
            """This is a regular reply with a code block in it:\
            \n```js\
            \nfunction foo() {\
            \n    ['1', '2', '3'].map(parseInt);\
            \n}\
            \n```""",
            42_000_000_003,
            42_000_000_000,
            False,
        )
    )

    fake_tree = CommentTree(
        fake_comments, CommentTreeSortOption.RELEVANCE, request.user
    )

    return {
        **generate_theme_chooser_dict(request),
        "fake_topics": fake_topics,
        "fake_comment_tree": fake_tree,
        "comment_label_options": [label for label in CommentLabelOption],
        "last_visit": fake_last_visit_timestamp,
    }
