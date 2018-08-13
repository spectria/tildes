"""Web API exception views."""

from typing import Sequence

from marshmallow.exceptions import ValidationError
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound,
    HTTPTooManyRequests,
    HTTPUnprocessableEntity,
)
from pyramid.request import Request
from pyramid.response import Response

from tildes.resources.comment import comment_by_id36
from tildes.resources.topic import topic_by_id36
from tildes.views.decorators import ic_view_config


def _422_response_with_errors(errors: Sequence[str]) -> Response:
    response = Response("\n".join(errors))
    response.status_int = 422

    return response


@ic_view_config(context=HTTPUnprocessableEntity)
@ic_view_config(context=ValidationError)
def unprocessable_entity(request: Request) -> Response:
    """Exception view for 422 errors."""
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

    errors_by_field = validation_error.messages

    error_strings = []
    for field, errors in errors_by_field.items():
        joined_errors = " ".join(errors)
        if field != "_schema":
            error_strings.append(f"{field}: {joined_errors}")
        else:
            error_strings.append(joined_errors)

    return _422_response_with_errors(error_strings)


@ic_view_config(context=ValueError)
def valueerror(request: Request) -> Response:
    """Convert a ValueError to a 422 response."""
    return _422_response_with_errors([request.exception.args[0]])


@ic_view_config(context=HTTPNotFound)
def httpnotfound(request: Request) -> Response:
    """Convert a 404 error to a text response (instead of HTML)."""
    response = request.exception

    if request.matched_route.factory == comment_by_id36:
        response.text = "Comment not found (or it was deleted)"
    elif request.matched_route.factory == topic_by_id36:
        response.text = "Topic not found (or it was deleted)"
    else:
        response.text = "Not found"

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
