# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views related to registration."""

from marshmallow.fields import String
from pyramid.httpexceptions import HTTPFound, HTTPUnprocessableEntity
from pyramid.request import Request
from pyramid.security import NO_PERMISSION_REQUIRED, remember
from pyramid.view import view_config
from sqlalchemy.exc import IntegrityError
from webargs.pyramidparser import use_kwargs

from tildes.enums import LogEventType
from tildes.lib.message import WELCOME_MESSAGE_SUBJECT, WELCOME_MESSAGE_TEXT
from tildes.metrics import incr_counter
from tildes.models.group import Group, GroupSubscription
from tildes.models.log import Log
from tildes.models.message import MessageConversation
from tildes.models.user import User, UserInviteCode
from tildes.schemas.user import UserSchema
from tildes.views.decorators import not_logged_in, rate_limit_view


@view_config(
    route_name="register", renderer="register.jinja2", permission=NO_PERMISSION_REQUIRED
)
@use_kwargs({"code": String(missing="")})
@not_logged_in
def get_register(request: Request, code: str) -> dict:
    """Display the registration form."""
    # pylint: disable=unused-argument
    return {"code": code}


def user_schema_check_breaches(request: Request) -> UserSchema:
    """Return a UserSchema that will check the password against breaches.

    It would probably be good to generalize this function at some point, probably
    similar to:
    http://webargs.readthedocs.io/en/latest/advanced.html#reducing-boilerplate
    """
    # pylint: disable=unused-argument
    return UserSchema(
        only=("username", "password"), context={"check_breached_passwords": True}
    )


@view_config(
    route_name="register", request_method="POST", permission=NO_PERMISSION_REQUIRED
)
@use_kwargs(user_schema_check_breaches)
@use_kwargs(
    {"invite_code": String(required=True), "password_confirm": String(required=True)}
)
@not_logged_in
@rate_limit_view("register")
def post_register(
    request: Request,
    username: str,
    password: str,
    password_confirm: str,
    invite_code: str,
) -> HTTPFound:
    """Process a registration request."""
    if not request.params.get("accepted_terms"):
        raise HTTPUnprocessableEntity(
            "Terms of Use and Privacy Policy must be accepted."
        )

    if password != password_confirm:
        raise HTTPUnprocessableEntity("Password and confirmation do not match.")

    # attempt to fetch and lock the row for the specified invite code (lock prevents
    # concurrent requests from using the same invite code)
    lookup_code = UserInviteCode.prepare_code_for_lookup(invite_code)
    code_row = (
        request.query(UserInviteCode)
        .filter(
            UserInviteCode.code == lookup_code,
            UserInviteCode.invitee_id == None,  # noqa
        )
        .with_for_update(skip_locked=True)
        .one_or_none()
    )

    if not code_row:
        incr_counter("invite_code_failures")
        raise HTTPUnprocessableEntity("Invalid invite code")

    # create the user and set inviter to the owner of the invite code
    user = User(username, password)
    user.inviter_id = code_row.user_id

    # flush the user insert to db, will fail if username is already taken
    request.db_session.add(user)
    try:
        request.db_session.flush()
    except IntegrityError:
        raise HTTPUnprocessableEntity("That username has already been registered.")

    # the flush above will generate the new user's ID, so use that to update the invite
    # code with info about the user that registered with it
    code_row.invitee_id = user.user_id

    # subscribe the new user to all groups except ~test
    all_groups = request.query(Group).all()
    for group in all_groups:
        if group.path == "test":
            continue
        request.db_session.add(GroupSubscription(user, group))

    _send_welcome_message(user, request)

    incr_counter("registrations")

    # log the user in to the new account
    remember(request, user.user_id)

    # set request.user before logging so the user is associated with the event
    request.user = user
    request.db_session.add(Log(LogEventType.USER_REGISTER, request))

    # redirect to the front page
    raise HTTPFound(location="/")


def _send_welcome_message(recipient: User, request: Request) -> None:
    """Send the welcome message if a sender is configured in the INI."""
    sender_username = request.registry.settings.get("tildes.welcome_message_sender")
    if not sender_username:
        return

    sender = request.query(User).filter(User.username == sender_username).one_or_none()
    if not sender:
        return

    welcome_message = MessageConversation(
        sender, recipient, WELCOME_MESSAGE_SUBJECT, WELCOME_MESSAGE_TEXT
    )
    request.db_session.add(welcome_message)
