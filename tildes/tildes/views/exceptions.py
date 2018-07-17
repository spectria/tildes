"""Views used by Pyramid when an exception is raised."""

from pyramid.request import Request
from pyramid.view import forbidden_view_config


@forbidden_view_config(xhr=False, renderer='error_403.jinja2')
def forbidden(request: Request) -> dict:
    """403 Forbidden page."""
    request.response.status_int = 403
    return {}
