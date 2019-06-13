# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Views related to group wiki pages."""

from pyramid.httpexceptions import HTTPFound
from pyramid.request import Request
from pyramid.view import view_config
from webargs.pyramidparser import use_kwargs

from tildes.models.group import GroupWikiPage
from tildes.schemas.fields import SimpleString
from tildes.schemas.group_wiki_page import GroupWikiPageSchema


@view_config(route_name="group_wiki", renderer="group_wiki.jinja2")
def get_group_wiki(request: Request) -> dict:
    """Get the group wiki page list."""
    group = request.context

    page_list = (
        request.query(GroupWikiPage)
        .filter(GroupWikiPage.group == group)
        .order_by(GroupWikiPage.slug)
        .all()
    )

    return {"group": group, "page_list": page_list}


@view_config(route_name="group_wiki_page", renderer="group_wiki_page.jinja2")
def get_group_wiki_page(request: Request) -> dict:
    """Display a single group wiki page."""
    page = request.context

    page_list = (
        request.query(GroupWikiPage)
        .filter(GroupWikiPage.group == page.group)
        .order_by(GroupWikiPage.slug)
        .all()
    )

    # remove the index from the page list, we'll output it separately
    if any(page.slug == "index" for page in page_list):
        has_index_page = True
        page_list = [page for page in page_list if page.slug != "index"]
    else:
        has_index_page = False

    return {"page": page, "page_list": page_list, "has_index_page": has_index_page}


@view_config(
    route_name="group_wiki_new_page",
    renderer="group_wiki_new_page.jinja2",
    permission="wiki_page_create",
)
def get_wiki_new_page_form(request: Request) -> dict:
    """Form for entering a new wiki page to create."""
    group = request.context

    return {"group": group}


@view_config(
    route_name="group_wiki", request_method="POST", permission="wiki_page_create"
)
@use_kwargs(GroupWikiPageSchema())
def post_group_wiki(request: Request, page_name: str, markdown: str) -> HTTPFound:
    """Create a new wiki page in a group."""
    group = request.context

    new_page = GroupWikiPage(group, page_name, markdown, request.user)

    request.db_session.add(new_page)

    raise HTTPFound(
        location=request.route_url(
            "group_wiki_page", group_path=group.path, wiki_page_slug=new_page.slug
        )
    )


@view_config(
    route_name="group_wiki_edit_page",
    renderer="group_wiki_edit_page.jinja2",
    permission="edit",
)
def get_wiki_edit_page_form(request: Request) -> dict:
    """Form for editing an existing wiki page."""
    page = request.context

    return {"page": page}


@view_config(route_name="group_wiki_page", request_method="POST", permission="edit")
@use_kwargs(GroupWikiPageSchema(only=("markdown",)))
@use_kwargs({"edit_message": SimpleString(max_length=80)})
def post_group_wiki_page(request: Request, markdown: str, edit_message: str) -> dict:
    """Apply an edit to a single group wiki page."""
    page = request.context

    page.edit(markdown, request.user, edit_message)

    raise HTTPFound(
        location=request.route_url(
            "group_wiki_page", group_path=page.group.path, wiki_page_slug=page.slug
        )
    )
