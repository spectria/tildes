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
    "aljazeera.com": SiteInfo("Al Jazeera"),
    "apnews.com": SiteInfo("Associated Press"),
    "arstechnica.com": SiteInfo("Ars Technica"),
    "axios.com": SiteInfo("Axios"),
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
    "forbes.com": SiteInfo("Forbes"),
    "gamasutra.com": SiteInfo("Gamasutra"),
    "github.com": SiteInfo("GitHub", show_author=True, content_type=None),
    "gq.com": SiteInfo("GQ"),
    "hpe.com": SiteInfo("Hewlett Packard Enterprise"),
    "huffpost.com": SiteInfo("HuffPost"),
    "imgur.com": SiteInfo("Imgur", content_type=TopicContentType.IMAGE),
    "justice.gov": SiteInfo("US Department of Justice"),
    "kotaku.com": SiteInfo("Kotaku"),
    "latimes.com": SiteInfo("Los Angeles Times"),
    "medium.com": SiteInfo("Medium", show_author=True),
    "mozilla.org": SiteInfo("Mozilla"),
    "nasa.gov": SiteInfo("NASA"),
    "nature.com": SiteInfo("Nature"),
    "nbcnews.com": SiteInfo("NBC News"),
    "newyorker.com": SiteInfo("The New Yorker"),
    "npr.org": SiteInfo("NPR"),
    "nytimes.com": SiteInfo("The New York Times"),
    "pinknews.co.uk": SiteInfo("PinkNews"),
    "polygon.com": SiteInfo("Polygon"),
    "propublica.org": SiteInfo("ProPublica"),
    "psmag.com": SiteInfo("Pacific Standard"),
    "quantamagazine.org": SiteInfo("Quanta Magazine"),
    "qz.com": SiteInfo("Quartz"),
    "reddit.com": SiteInfo("reddit", content_type=None),
    "reuters.com": SiteInfo("Reuters"),
    "rockpapershotgun.com": SiteInfo("Rock Paper Shotgun"),
    "sciencemag.org": SiteInfo("Science"),
    "seriouseats.com": SiteInfo("Serious Eats"),
    "sfchronicle.com": SiteInfo("San Francisco Chronicle"),
    "slate.com": SiteInfo("Slate"),
    "smh.com.au": SiteInfo("The Sydney Morning Herald"),
    "soundcloud.com": SiteInfo("SoundCloud", show_author=True, content_type=None),
    "techcrunch.com": SiteInfo("TechCrunch"),
    "technologyreview.com": SiteInfo("MIT Technology Review"),
    "telegraph.co.uk": SiteInfo("The Telegraph"),
    "theatlantic.com": SiteInfo("The Atlantic"),
    "theconversation.com": SiteInfo("The Conversation"),
    "theguardian.com": SiteInfo("The Guardian"),
    "thehill.com": SiteInfo("The Hill"),
    "theoutline.com": SiteInfo("The Outline"),
    "theverge.com": SiteInfo("The Verge"),
    "twitter.com": SiteInfo(
        "Twitter", show_author=True, content_type=TopicContentType.TWEET
    ),
    "usatoday.com": SiteInfo("USA Today"),
    "variety.com": SiteInfo("Variety"),
    "vice.com": SiteInfo("VICE"),
    "vimeo.com": SiteInfo(
        "Vimeo", show_author=True, content_type=TopicContentType.VIDEO
    ),
    "vox.com": SiteInfo("Vox"),
    "washingtonpost.com": SiteInfo("The Washington Post"),
    "who.int": SiteInfo("World Health Organization"),
    "wired.com": SiteInfo("WIRED"),
    "wordpress.com": SiteInfo("WordPress", show_author=True),
    "wsj.com": SiteInfo("The Wall Street Journal"),
    "youtube.com": SiteInfo(
        "YouTube", show_author=True, content_type=TopicContentType.VIDEO
    ),
}
