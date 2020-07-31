# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Web API endpoint for previewing Markdown."""

from pyramid.request import Request

from tildes.lib.markdown import convert_markdown_to_safe_html
from tildes.schemas.group_wiki_page import GroupWikiPageSchema
from tildes.views.decorators import ic_view_config, use_kwargs


@ic_view_config(
    route_name="markdown_preview",
    request_method="POST",
    renderer="markdown_preview.jinja2",
)
# uses GroupWikiPageSchema because it should always have the highest max_length
@use_kwargs(GroupWikiPageSchema(only=("markdown",)), location="form")
def markdown_preview(request: Request, markdown: str) -> dict:
    """Render the provided text as Markdown."""
    # pylint: disable=unused-argument

    rendered_html = convert_markdown_to_safe_html(markdown)
    return {"rendered_html": rendered_html}
