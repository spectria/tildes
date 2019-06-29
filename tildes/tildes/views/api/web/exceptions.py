# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Web API exception views."""

from typing import Sequence

from marshmallow.exceptions import ValidationError
from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPFound,
    HTTPNotFound,
    HTTPTooManyRequests,
    HTTPUnprocessableEntity,
)
from pyramid.request import Request
from pyramid.response import Response

from tildes.views.decorators import ic_view_config
from tildes.views.exceptions import errors_from_validationerror


def _422_response_with_errors(errors: Sequence[str]) -> Response:
    response = Response("\n".join(errors))
    response.status_int = 422

    return response


@ic_view_config(context=HTTPUnprocessableEntity)
@ic_view_config(context=ValidationError)
def unprocessable_entity(request: Request) -> Response:
    """Exception view for 422 errors."""
    # pylint: disable=too-many-branches
    if isinstance(request.exception, ValidationError):
        validation_error = request.exception
    else:
        # see if there's an underlying ValidationError using exception chain
        validation_error = request.exception.__context__
        if not isinstance(validation_error, ValidationError):
            validation_error = None

    # if no ValidationError, we can just use the exception's message directly
    if not validation_error:
        return _422_response_with_errors([str(request.exception)])

    error_strings = errors_from_validationerror(validation_error)

    return _422_response_with_errors(error_strings)


@ic_view_config(context=ValueError)
def valueerror(request: Request) -> Response:
    """Convert a ValueError to a 422 response."""
    return _422_response_with_errors([request.exception.args[0]])


# I can't get a "general" view with context=HTTPError to work for some reason, so
# this just specifically catches the errors that people have encountered.
@ic_view_config(context=HTTPBadRequest)
@ic_view_config(context=HTTPForbidden)
@ic_view_config(context=HTTPNotFound)
def error_to_text_response(request: Request) -> Response:
    """Convert HTML error to a text response for Intercooler to display."""
    # pylint: disable=too-many-branches
    response = request.exception

    if isinstance(request.exception, HTTPNotFound):
        if response.message:
            response.text = response.message
        else:
            response.text = "Not found"
    elif isinstance(request.exception, HTTPForbidden):
        response.text = "Access denied (try reloading)"
    elif isinstance(request.exception, HTTPBadRequest):
        if response.title == "Bad CSRF Token":
            response.text = "Page expired, reload and try again"
        else:
            response.text = "Unknown error"

    return response


@ic_view_config(context=HTTPTooManyRequests)
def httptoomanyrequests(request: Request) -> Response:
    """Update a 429 error to show wait time info in the response text."""
    response = request.exception

    retry_seconds = request.exception.headers["Retry-After"]
    response.text = (
        f"Rate limit exceeded. Please wait {retry_seconds} seconds before retrying."
    )

    return response


@ic_view_config(context=HTTPFound)
def httpfound(request: Request) -> Response:
    """Convert an HTTPFound to a 200 with the header for a redirect.

    Intercooler won't handle a 302 response as a "full" redirect, and will just load the
    content of the destination page into the target element, the same as any other
    response. However, it has support for a special X-IC-Redirect header, which allows
    the response to trigger a client-side redirect. This exception view will convert a
    302 into a 200 with that header so it works as a redirect for both standard requests
    as well as Intercooler ones.
    """
    return Response(headers={"X-IC-Redirect": request.exception.location})
