# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions related to URLs."""

from urllib.parse import urlparse


def get_domain_from_url(url: str, strip_www: bool = True) -> str:
    """Return the domain name from a url."""
    domain = urlparse(url).netloc

    if not domain:
        raise ValueError("Invalid url or domain could not be determined")

    if strip_www and domain.startswith("www."):
        domain = domain[4:]

    return domain


def is_tweet(url: str) -> bool:
    """Return whether a url is a link to a tweet."""
    domain = get_domain_from_url(url)
    return domain == "twitter.com" and "/status/" in url
