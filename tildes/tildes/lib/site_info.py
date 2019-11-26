# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Library code related to displaying info about individual websites."""

from typing import List, Optional

from tildes.enums import ContentMetadataFields, TopicContentType


class SiteInfo:
    """Class containing various info about a particular site."""

    def __init__(
        self,
        name: str,
        show_author: bool = False,
        content_type: Optional[TopicContentType] = None,
    ) -> None:
        """Initialize info for a site."""
        self.name = name
        self.show_author = show_author
        self.content_type = content_type

    def content_source(self, authors: Optional[List[str]] = None) -> str:
        """Return a string representing the "source" of content on this site.

        If the site isn't one that needs to show its author, this is just its name.
        """
        if self.show_author and authors:
            authors_str = ContentMetadataFields.AUTHORS.format_value(authors)
            return f"{self.name}: {authors_str}"

        return self.name


SITE_INFO_BY_DOMAIN = {
    "medium.com": SiteInfo(
        "Medium", show_author=True, content_type=TopicContentType.ARTICLE
    ),
    "twitter.com": SiteInfo(
        "Twitter", show_author=True, content_type=TopicContentType.TWEET
    ),
    "vimeo.com": SiteInfo(
        "Vimeo", show_author=True, content_type=TopicContentType.VIDEO
    ),
    "youtube.com": SiteInfo(
        "YouTube", show_author=True, content_type=TopicContentType.VIDEO
    ),
}
