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
    "animenewsnetwork.com": SiteInfo("Anime News Network"),
    "apnews.com": SiteInfo("Associated Press"),
    "appleinsider.com": SiteInfo("AppleInsider"),
    "arstechnica.com": SiteInfo("Ars Technica"),
    "atlasobsura.com": SiteInfo("Atlas Obscura"),
    "axios.com": SiteInfo("Axios"),
    "bandcamp.com": SiteInfo("Bandcamp", content_type=None),
    "bbc.co.uk": SiteInfo("BBC"),
    "bbc.com": SiteInfo("BBC"),
    "bellingcat.com": SiteInfo("Bellingcat"),
    "bloomberg.com": SiteInfo("Bloomberg"),
    "businessinsider.com": SiteInfo("Business Insider"),
    "buzzfeednews.com": SiteInfo("BuzzFeed News"),
    "cbc.ca": SiteInfo("CBC"),
    "cbssports.com": SiteInfo("CBS Sports"),
    "citylab.com": SiteInfo("CityLab"),
    "cjr.org": SiteInfo("Columbia Journalism Review"),
    "cnbc.com": SiteInfo("CNBC"),
    "cnet.com": SiteInfo("CNET"),
    "cnn.com": SiteInfo("CNN"),
    "currentaffairs.org": SiteInfo("Current Affairs"),
    "deadline.com": SiteInfo("Deadline"),
    "dev.to": SiteInfo("DEV"),
    "dw.com": SiteInfo("DW"),
    "eater.com": SiteInfo("Eater"),
    "eff.org": SiteInfo("Electronic Frontier Foundation"),
    "egmnow.com": SiteInfo("EGM"),
    "eurogamer.net": SiteInfo("Eurogamer"),
    "fastcompany.com": SiteInfo("Fast Company"),
    "fivethirtyeight.com": SiteInfo("FiveThirtyEight"),
    "forbes.com": SiteInfo("Forbes"),
    "ftc.gov": SiteInfo("Federal Trade Commission"),
    "gamasutra.com": SiteInfo("Gamasutra"),
    "gamesindustry.biz": SiteInfo("GamesIndustry.biz"),
    "github.com": SiteInfo("GitHub", show_author=True, content_type=None),
    "gizmodo.com": SiteInfo("Gizmodo"),
    "gq.com": SiteInfo("GQ"),
    "hackaday.com": SiteInfo("Hackaday"),
    "hackernoon.com": SiteInfo("Hacker Noon"),
    "hpe.com": SiteInfo("Hewlett Packard Enterprise"),
    "huffpost.com": SiteInfo("HuffPost"),
    "imgur.com": SiteInfo("Imgur", content_type=TopicContentType.IMAGE),
    "independent.co.uk": SiteInfo("The Independent"),
    "jacobinmag.com": SiteInfo("Jacobin"),
    "justice.gov": SiteInfo("US Department of Justice"),
    "kickstarter.com": SiteInfo("Kickstarter", show_author=True, content_type=None),
    "kotaku.com": SiteInfo("Kotaku"),
    "latimes.com": SiteInfo("Los Angeles Times"),
    "lithub.com": SiteInfo("Literary Hub"),
    "lwn.net": SiteInfo("LWN"),
    "medium.com": SiteInfo("Medium", show_author=True),
    "melmagazine.com": SiteInfo("MEL Magazine"),
    "mozilla.org": SiteInfo("Mozilla"),
    "nasa.gov": SiteInfo("NASA"),
    "nationalgeographic.com": SiteInfo("National Geographic"),
    "nature.com": SiteInfo("Nature"),
    "nbcnews.com": SiteInfo("NBC News"),
    "newsweek.com": SiteInfo("Newsweek"),
    "newyorker.com": SiteInfo("The New Yorker"),
    "npr.org": SiteInfo("NPR"),
    "nymag.com": SiteInfo("New York Magazine"),
    "nytimes.com": SiteInfo("The New York Times"),
    "outsideonline.com": SiteInfo("Outside"),
    "pcgamer.com": SiteInfo("PC Gamer"),
    "pinknews.co.uk": SiteInfo("PinkNews"),
    "politico.com": SiteInfo("Politico"),
    "politico.eu": SiteInfo("Politico Europe"),
    "polygon.com": SiteInfo("Polygon"),
    "popsci.com": SiteInfo("Popular Science"),
    "propublica.org": SiteInfo("ProPublica"),
    "psmag.com": SiteInfo("Pacific Standard"),
    "quantamagazine.org": SiteInfo("Quanta Magazine"),
    "qz.com": SiteInfo("Quartz"),
    "reddit.com": SiteInfo("reddit", content_type=None),
    "reuters.com": SiteInfo("Reuters"),
    "rockpapershotgun.com": SiteInfo("Rock Paper Shotgun"),
    "rollingstone.com": SiteInfo("Rolling Stone"),
    "sciencemag.org": SiteInfo("Science"),
    "seattletimes.com": SiteInfo("The Seattle Times"),
    "seriouseats.com": SiteInfo("Serious Eats"),
    "sfchronicle.com": SiteInfo("San Francisco Chronicle"),
    "si.com": SiteInfo("Sports Illustrated"),
    "slate.com": SiteInfo("Slate"),
    "smh.com.au": SiteInfo("The Sydney Morning Herald"),
    "smithsonianmag.com": SiteInfo("Smithsonian"),
    "soundcloud.com": SiteInfo("SoundCloud", show_author=True, content_type=None),
    "spacenews.com": SiteInfo("SpaceNews"),
    "steamcommunity.com": SiteInfo("Steam"),
    "steampowered.com": SiteInfo("Steam", content_type=None),
    "stratechery.com": SiteInfo("Stratechery"),
    "substack.com": SiteInfo("Substack", show_author=True),
    "techcrunch.com": SiteInfo("TechCrunch"),
    "techdirt.com": SiteInfo("Techdirt"),
    "technologyreview.com": SiteInfo("MIT Technology Review"),
    "ted.com": SiteInfo("TED"),
    "teenvogue.com": SiteInfo("Teen Vogue"),
    "telegraph.co.uk": SiteInfo("The Telegraph"),
    "theatlantic.com": SiteInfo("The Atlantic"),
    "thebaffler.com": SiteInfo("The Baffler"),
    "theconversation.com": SiteInfo("The Conversation"),
    "thecorrespondent.com": SiteInfo("The Correspondent"),
    "thedrive.com": SiteInfo("The Drive"),
    "theguardian.com": SiteInfo("The Guardian"),
    "thehill.com": SiteInfo("The Hill"),
    "theinformation.com": SiteInfo("The Information"),
    "theoutline.com": SiteInfo("The Outline"),
    "theparisreview.org": SiteInfo("Paris Review"),
    "theregister.co.uk": SiteInfo("The Register"),
    "theringer.com": SiteInfo("The Ringer"),
    "theverge.com": SiteInfo("The Verge"),
    "threadreaderapp.com": SiteInfo(
        "Twitter (via Thread Reader)", content_type=TopicContentType.TWEET
    ),
    "time.com": SiteInfo("TIME"),
    "tortoisemedia.com": SiteInfo("Tortoise"),
    "twitter.com": SiteInfo(
        "Twitter", show_author=True, content_type=TopicContentType.TWEET
    ),
    "usatoday.com": SiteInfo("USA Today"),
    "vanityfair.com": SiteInfo("Vanity Fair"),
    "variety.com": SiteInfo("Variety"),
    "vice.com": SiteInfo("VICE"),
    "vimeo.com": SiteInfo(
        "Vimeo", show_author=True, content_type=TopicContentType.VIDEO
    ),
    "vox.com": SiteInfo("Vox"),
    "vulture.com": SiteInfo("Vulture"),
    "washingtonpost.com": SiteInfo("The Washington Post"),
    "who.int": SiteInfo("World Health Organization"),
    "wikipedia.org": SiteInfo("Wikipedia"),
    "wired.com": SiteInfo("WIRED"),
    "wordpress.com": SiteInfo("WordPress", show_author=True),
    "wsj.com": SiteInfo("The Wall Street Journal"),
    "yahoo.com": SiteInfo("Yahoo"),
    "youtube.com": SiteInfo(
        "YouTube", show_author=True, content_type=TopicContentType.VIDEO
    ),
    "zdnet.com": SiteInfo("ZDNet"),
}
