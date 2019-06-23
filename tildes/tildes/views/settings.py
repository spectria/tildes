# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views related to user settings."""

from io import BytesIO

import pyotp
import qrcode
from pyramid.httpexceptions import HTTPForbidden, HTTPUnprocessableEntity
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_config
from webargs.pyramidparser import use_kwargs

from tildes.lib.string import separate_string
from tildes.schemas.user import (
    BIO_MAX_LENGTH,
    EMAIL_ADDRESS_NOTE_MAX_LENGTH,
    UserSchema,
)


PASSWORD_FIELD = UserSchema(only=("password",)).fields["password"]


@view_config(route_name="settings", renderer="settings.jinja2")
def get_settings(request: Request) -> dict:
    """Generate the user settings page."""
    site_default_theme = "white"
    user_default_theme = request.user.theme_default or site_default_theme

    current_theme = request.cookies.get("theme", "") or user_default_theme

    theme_options = {
        "white": "White",
        "light": "Solarized Light",
        "dark": "Solarized Dark",
        "dracula": "Dracula",
        "atom-one-dark": "Atom One Dark",
        "black": "Black",
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
