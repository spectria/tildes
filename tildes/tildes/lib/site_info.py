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
        content_type: Optional[TopicContentType] = TopicContentType.ARTICLE,
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
    "abc.net.au": SiteInfo("ABC"),
    "aeon.co": SiteInfo("Aeon"),
    "apnews.com": SiteInfo("Associated Press"),
    "arstechnica.com": SiteInfo("Ars Technica"),
    "bandcamp.com": SiteInfo("Bandcamp", content_type=None),
    "bbc.co.uk": SiteInfo("BBC"),
    "bbc.com": SiteInfo("BBC"),
    "bloomberg.com": SiteInfo("Bloomberg"),
    "buzzfeednews.com": SiteInfo("BuzzFeed News"),
    "cbc.ca": SiteInfo("CBC"),
    "citylab.com": SiteInfo("CityLab"),
    "cnbc.com": SiteInfo("CNBC"),
    "cnn.com": SiteInfo("CNN"),
    "dw.com": SiteInfo("DW"),
    "eurogamer.net": SiteInfo("Eurogamer"),
    "github.com": SiteInfo("GitHub", show_author=True, content_type=None),
    "hpe.com": SiteInfo("Hewlett Packard Enterprise"),
    "imgur.com": SiteInfo("Imgur", content_type=TopicContentType.IMAGE),
    "kotaku.com": SiteInfo("Kotaku"),
    "medium.com": SiteInfo("Medium", show_author=True),
    "mozilla.org": SiteInfo("Mozilla"),
    "nbcnews.com": SiteInfo("NBC News"),
    "newyorker.com": SiteInfo("The New Yorker"),
    "npr.org": SiteInfo("NPR"),
    "nytimes.com": SiteInfo("The New York Times"),
    "polygon.com": SiteInfo("Polygon"),
    "propublica.org": SiteInfo("ProPublica"),
    "psmag.com": SiteInfo("Pacific Standard"),
    "qz.com": SiteInfo("Quartz"),
    "reddit.com": SiteInfo("reddit", content_type=None),
    "reuters.com": SiteInfo("Reuters"),
    "slate.com": SiteInfo("Slate"),
    "smh.com.au": SiteInfo("The Sydney Morning Herald"),
    "soundcloud.com": SiteInfo("SoundCloud", show_author=True, content_type=None),
    "techcrunch.com": SiteInfo("TechCrunch"),
    "theatlantic.com": SiteInfo("The Atlantic"),
    "theconversation.com": SiteInfo("The Conversation"),
    "theguardian.com": SiteInfo("The Guardian"),
    "thehill.com": SiteInfo("The Hill"),
    "theverge.com": SiteInfo("The Verge"),
    "twitter.com": SiteInfo(
        "Twitter", show_author=True, content_type=TopicContentType.TWEET
    ),
    "variety.com": SiteInfo("Variety"),
    "vice.com": SiteInfo("VICE"),
    "vimeo.com": SiteInfo(
        "Vimeo", show_author=True, content_type=TopicContentType.VIDEO
    ),
    "vox.com": SiteInfo("Vox"),
    "washingtonpost.com": SiteInfo("The Washington Post"),
    "wired.com": SiteInfo("WIRED"),
    "wordpress.com": SiteInfo("WordPress", show_author=True),
    "wsj.com": SiteInfo("The Wall Street Journal"),
    "youtube.com": SiteInfo(
        "YouTube", show_author=True, content_type=TopicContentType.VIDEO
    ),
}
