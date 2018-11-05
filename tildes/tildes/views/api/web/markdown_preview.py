# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Web API endpoint for previewing Markdown."""

from pyramid.request import Request
from webargs.pyramidparser import use_kwargs

from tildes.lib.markdown import convert_markdown_to_safe_html
from tildes.schemas.comment import CommentSchema
from tildes.views.decorators import ic_view_config


@ic_view_config(
    route_name="markdown_preview",
    request_method="POST",
    renderer="markdown_preview.jinja2",
)
@use_kwargs(CommentSchema(only=("markdown",)))
def markdown_preview(request: Request, markdown: str) -> dict:
    """Render the provided text as Markdown."""
    # pylint: disable=unused-argument

    rendered_html = convert_markdown_to_safe_html(markdown)
    return {"rendered_html": rendered_html}
