"""Views related to logging in/out."""

from pyramid.httpexceptions import HTTPFound, HTTPUnprocessableEntity
from pyramid.request import Request
from pyramid.security import NO_PERMISSION_REQUIRED, remember
from pyramid.view import view_config
from webargs.pyramidparser import use_kwargs

from tildes.enums import LogEventType
from tildes.metrics import incr_counter
from tildes.models.log import Log
from tildes.models.user import User
from tildes.schemas.user import UserSchema
from tildes.views.decorators import not_logged_in, rate_limit_view


@view_config(
    route_name="login", renderer="login.jinja2", permission=NO_PERMISSION_REQUIRED
)
@not_logged_in
def get_login(request: Request) -> dict:
    """Display the login form."""
    # pylint: disable=unused-argument
    return {}


@view_config(
    route_name="login", request_method="POST", permission=NO_PERMISSION_REQUIRED
)
@use_kwargs(UserSchema(only=("username", "password"), strict=True))
@not_logged_in
@rate_limit_view("login")
def post_login(request: Request, username: str, password: str) -> HTTPFound:
    """Process a log in request."""
    incr_counter("logins")

    # Look up the user for the supplied username
    user = (
        request.query(User)
        .undefer_all_columns()
        .filter(User.username == username)
        .one_or_none()
    )

    # If that user doesn't exist or the password was wrong, error out
    if not user or not user.is_correct_password(password):
        incr_counter("login_failures")

        # log the failure - need to manually commit because of the exception
        log_entry = Log(LogEventType.USER_LOG_IN_FAIL, request, {"username": username})
        request.db_session.add(log_entry)
        request.tm.commit()

        raise HTTPUnprocessableEntity("Incorrect username or password")

    # Don't allow banned users to log in
    if user.is_banned:
        raise HTTPUnprocessableEntity("This account has been banned")

    # Username/password were correct - attach the user_id to the session
    remember(request, user.user_id)

    # Depending on "keep me logged in", set session timeout to 1 year or 1 day
    if request.params.get("keep"):
        request.session.adjust_timeout_for_session(31_536_000)
    else:
        request.session.adjust_timeout_for_session(86_400)

    # set request.user before logging so the user is associated with the event
    request.user = user
    request.db_session.add(Log(LogEventType.USER_LOG_IN, request))

    raise HTTPFound(location="/")


@view_config(route_name="logout")
def get_logout(request: Request) -> HTTPFound:
    """Process a log out request."""
    request.session.invalidate()
    request.db_session.add(Log(LogEventType.USER_LOG_OUT, request))

    raise HTTPFound(location="/")
