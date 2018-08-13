"""Views related to user settings."""

from pyramid.httpexceptions import HTTPUnprocessableEntity
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_config
from webargs.pyramidparser import use_kwargs

from tildes.schemas.user import EMAIL_ADDRESS_NOTE_MAX_LENGTH, UserSchema


PASSWORD_FIELD = UserSchema(only=("password",)).fields["password"]


@view_config(route_name="settings", renderer="settings.jinja2")
def get_settings(request: Request) -> dict:
    """Generate the user settings page."""
    current_theme = request.cookies.get("theme", "")
    theme_options = {
        "": "White (default)",
        "light": "Solarized Light",
        "dark": "Solarized Dark",
        "black": "Black",
    }

    return {"current_theme": current_theme, "theme_options": theme_options}


@view_config(
    route_name="settings_account_recovery", renderer="settings_account_recovery.jinja2"
)
def get_settings_account_recovery(request: Request) -> dict:
    """Generate the account recovery page."""
    # pylint: disable=unused-argument
    return {"note_max_length": EMAIL_ADDRESS_NOTE_MAX_LENGTH}


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
