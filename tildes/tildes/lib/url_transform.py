# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions related to transforming URLs (sanitization, cleanup, etc.)."""

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def apply_url_transformations(url: str) -> str:
    """Apply all applicable transformations to a url.

    This method should generally be the only one imported/used from this module, unless
    there is a specific reason for needing to apply a subset of transformations.
    """
    url = remove_utm_query_params(url)

    return url


def remove_utm_query_params(url: str) -> str:
    """Remove any utm_* query parameters from a url."""
    parsed = urlparse(url)

    query_params = parse_qs(parsed.query)

    cleaned_params = {
        param: value
        for param, value in query_params.items()
        if not param.startswith("utm_")
    }

    parsed = parsed._replace(query=urlencode(cleaned_params, doseq=True))

    return urlunparse(parsed)
