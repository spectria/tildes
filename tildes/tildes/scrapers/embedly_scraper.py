# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the EmbedlyScraper class."""

from typing import Any, Dict

import requests

from tildes.enums import ScraperType
from tildes.lib.string import extract_text_from_html, word_count
from tildes.models.scraper import ScraperResult


class EmbedlyScraper:
    """Scraper that uses Embedly's "Extract" API."""

    def __init__(self, api_key: str):
        """Create a new scraper using the specified Embedly API key."""
        self.api_key = api_key

    def scrape_url(self, url: str) -> ScraperResult:
        """Scrape a url and return the result."""
        params: Dict[str, Any] = {"key": self.api_key, "format": "json", "url": url}

        response = requests.get(
            "https://api.embedly.com/1/extract", params=params, timeout=5
        )
        response.raise_for_status()

        return ScraperResult(url, ScraperType.EMBEDLY, response.json())

    @staticmethod
    def get_metadata_from_result(result: ScraperResult) -> Dict[str, Any]:
        """Get the metadata that we're interested in out of a scrape result."""
        # pylint: disable=too-many-branches
        if result.scraper_type != ScraperType.EMBEDLY:
            raise ValueError("Can't process a result from a different scraper.")

        metadata = {}

        if result.data.get("title"):
            metadata["title"] = result.data["title"]

        if result.data.get("description"):
            metadata["description"] = result.data["description"]

        content = result.data.get("content")
        if content:
            metadata["word_count"] = word_count(extract_text_from_html(content))

        if result.data.get("published"):
            # the field's value is in milliseconds, store it in seconds instead
            metadata["published"] = result.data["published"] // 1000

        authors = result.data.get("authors")
        if authors:
            try:
                metadata["authors"] = [author["name"] for author in authors]
            except KeyError:
                pass

        return metadata
