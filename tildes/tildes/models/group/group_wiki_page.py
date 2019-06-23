# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the GroupWikiPage class."""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Sequence, Tuple

from pygit2 import Repository, Signature
from pyramid.security import Allow, DENY_ALL, Everyone
from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tildes.lib.database import CIText
from tildes.lib.datetime import utc_now
from tildes.lib.html import add_anchors_to_headings
from tildes.lib.markdown import convert_markdown_to_safe_html
from tildes.lib.string import convert_to_url_slug
from tildes.models import DatabaseModel
from tildes.models.user import User
from tildes.schemas.group_wiki_page import GroupWikiPageSchema, PAGE_NAME_MAX_LENGTH

from .group import Group


class GroupWikiPage(DatabaseModel):
    """Model for a wiki page in a group."""

    schema_class = GroupWikiPageSchema

    __tablename__ = "group_wiki_pages"

    BASE_PATH = "/var/lib/tildes-wiki"
    GITLAB_REPO_URL = "https://gitlab.com/tildes/tildes-wiki"

    group_id: int = Column(
        Integer, ForeignKey("groups.group_id"), nullable=False, primary_key=True
    )
    slug: str = Column(CIText, nullable=False, primary_key=True)
    page_name: str = Column(
        Text,
        CheckConstraint(
            f"LENGTH(page_name) <= {PAGE_NAME_MAX_LENGTH}", name="page_name_length"
        ),
        nullable=False,
    )
    created_time: datetime = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )
    last_edited_time: Optional[datetime] = Column(TIMESTAMP(timezone=True), index=True)
    rendered_html: str = Column(Text, nullable=False)

    group: Group = relationship("Group", innerjoin=True, lazy=False)

    def __init__(self, group: Group, page_name: str, markdown: str, user: User):
        """Create a new wiki page."""
        self.group = group
        self.page_name = page_name
        self.slug = convert_to_url_slug(page_name)

        # prevent possible conflict with url for creating a new page
        if self.slug == "new_page":
            raise ValueError("Invalid page name")

        if self.file_path.exists():
            raise ValueError("Wiki page already exists")

        # create the directory for the group if it doesn't already exist
        self.file_path.parent.mkdir(mode=0o755, exist_ok=True)

        self.edit(markdown, user, "Create page")

    def __acl__(self) -> Sequence[Tuple[str, Any, str]]:
        """Pyramid security ACL."""
        acl = []

        # view:
        #  - all wiki pages can be viewed by everyone
        acl.append((Allow, Everyone, "view"))

        # edit:
        #  - permission must be granted specifically
        acl.append((Allow, "admin", "edit"))
        acl.append((Allow, "wiki", "edit"))

        acl.append(DENY_ALL)

        return acl

    @property
    def file_path(self) -> Path:
        """Return the full path to the page's file."""
        return Path(self.BASE_PATH, self.relative_path)

    @property
    def relative_path(self) -> Path:
        """Return a relative path to the page's file."""
        return Path(str(self.group.path), f"{self.slug}.md")

    @property
    def history_url(self) -> str:
        """Return a url to the page's edit history."""
        return f"{self.GITLAB_REPO_URL}/commits/master/{self.relative_path}"

    @property
    def blame_url(self) -> str:
        """Return a url to the page's blame view."""
        return f"{self.GITLAB_REPO_URL}/blame/master/{self.relative_path}"

    @property
    def markdown(self) -> Optional[str]:
        """Return the wiki page's markdown."""
        try:
            return self.file_path.read_text().rstrip("\r\n")
        except FileNotFoundError:
            return None

    @markdown.setter
    def markdown(self, new_markdown: str) -> None:
        """Write the wiki page's markdown to its file."""
        # write the markdown to the file, appending a newline if necessary
        if not new_markdown.endswith("\n"):
            new_markdown = new_markdown + "\n"

        self.file_path.write_text(new_markdown)

    def edit(self, new_markdown: str, user: User, edit_message: str) -> None:
        """Set the page's markdown, render its HTML, and commit the repo."""
        if new_markdown == self.markdown:
            return

        self.markdown = new_markdown
        self.rendered_html = convert_markdown_to_safe_html(new_markdown)
        self.rendered_html = add_anchors_to_headings(self.rendered_html)
        self.last_edited_time = utc_now()

        repo = Repository(self.BASE_PATH)
        author = Signature(user.username, user.username)

        repo.index.read()
        repo.index.add(str(self.file_path.relative_to(self.BASE_PATH)))
        repo.index.write()

        # Prepend the group name and page slug to the edit message - if you change the
        # format of this, make sure to also change the page-editing template to match
        edit_message = f"~{self.group.path}/{self.slug}: {edit_message}"

        repo.create_commit(
            repo.head.name,
            author,
            author,
            edit_message,
            repo.index.write_tree(),
            [repo.head.target],
        )
