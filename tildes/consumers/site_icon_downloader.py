# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Consumer that downloads site icons using Embedly scraper data."""

from collections.abc import Sequence
from io import BytesIO
from os import path
from typing import Optional

import publicsuffix
import requests
from PIL import Image

from tildes.enums import ScraperType
from tildes.lib.event_stream import EventStreamConsumer, Message
from tildes.lib.url import get_domain_from_url
from tildes.models.scraper import ScraperResult


class SiteIconDownloader(EventStreamConsumer):
    """Consumer that generates content_metadata for topics."""

    METRICS_PORT = 25011

    ICON_FOLDER = "/opt/tildes/static/images/site-icons"

    def __init__(self, consumer_group: str, source_streams: Sequence[str]):
        """Initialize the consumer, including the public suffix list."""
        super().__init__(consumer_group, source_streams)

        # download the public suffix list (would be good to add caching here)
        psl_file = publicsuffix.fetch()
        self.public_suffix_list = publicsuffix.PublicSuffixList(psl_file)

    def process_message(self, message: Message) -> None:
        """Process a message from the stream."""
        result = (
            self.db_session.query(ScraperResult)
            .filter_by(result_id=message.fields["result_id"])
            .one()
        )

        # Check if we already have an icon for this domain, and skip if we do. This
        # currently uses the ScraperResult's url, but it might be better to use the
        # Embedly url data, since that will be after any redirects
        parsed_domain = get_domain_from_url(result.url)
        domain = self.public_suffix_list.get_public_suffix(parsed_domain)

        filename = domain.replace(".", "_") + ".png"
        filename = path.join(self.ICON_FOLDER, filename)
        if path.exists(filename):
            return

        if result.scraper_type != ScraperType.EMBEDLY:
            return

        favicon_url = result.data.get("favicon_url")
        if not favicon_url:
            return

        try:
            response = requests.get(favicon_url, timeout=5)
        except requests.exceptions.RequestException:
            return

        if response.status_code != 200:
            return

        icon = self._get_icon_from_response(response)
        if icon:
            icon.save(filename)

    @staticmethod
    def _get_icon_from_response(response: requests.Response) -> Optional[Image.Image]:
        """Return a properly-sized icon Image extracted from a Response."""
        try:
            favicon = Image.open(BytesIO(response.content))
        except (OSError, ValueError):
            return None

        if favicon.format == "ICO":
            # get the 32x32 size if it's present, otherwise resize the largest one
            if (32, 32) in favicon.ico.sizes():
                return favicon.ico.getimage((32, 32))

            image = favicon.ico.getimage(max(favicon.ico.sizes()))
            return image.resize((32, 32))
        elif favicon.format in ("JPEG", "PNG"):
            image = favicon
            if image.size != (32, 32):
                image = image.resize((32, 32))

            return image

        # any other formats aren't handled
        return None


if __name__ == "__main__":
    SiteIconDownloader(
        "site_icon_downloader", source_streams=["scraper_results.insert"]
    ).consume_streams()
