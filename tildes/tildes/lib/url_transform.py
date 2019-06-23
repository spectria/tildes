# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions related to transforming URLs (sanitization, cleanup, etc.)."""

import logging
from abc import ABC, abstractmethod
from collections import Counter
from urllib.parse import (
    parse_qs,
    parse_qsl,
    ParseResult,
    urlencode,
    urlparse,
    urlunparse,
)


class UrlTransformationLoopError(Exception):
    """Exception to raise if transformations seem to be in an infinite loop."""

    pass


def apply_url_transformations(url: str) -> str:
    """Apply all applicable transformations to a url.

    This method should generally be the only one imported/used from this module, unless
    there is a specific reason for needing to apply a subset of transformations.
    """
    parsed_url = urlparse(url)

    if _is_exempt_from_transformations(parsed_url):
        return url

    try:
        parsed_url = _apply_all_transformations(parsed_url)
    except UrlTransformationLoopError:
        # if an infinite loop was caused, log an error and return the unchanged original
        logging.error(f"Transformations went into a loop on url {url}")

    return urlunparse(parsed_url)


def _is_exempt_from_transformations(parsed_url: ParseResult) -> bool:
    """Return whether this url should be exempt from the transformation process."""
    if not parsed_url.hostname:
        return True

    # Paradox forums use an invalid url scheme that will break if processed
    if parsed_url.hostname == "forum.paradoxplaza.com":
        return True

    return False


def _apply_all_transformations(parsed_url: ParseResult) -> ParseResult:
    """Apply all relevant UrlTransformer transformations to the url."""
    # Used to keep track of which transformations are restarting the process, so we
    # can detect cases where the process has gone into a loop (such as if two of them
    # are reversing each other's changes repeatedly)
    restarted_by: Counter = Counter()

    # This structure is confusing - its purpose is to restart the full set of
    # transformations whenever any of them cause the url to be changed, and only stop
    # when all of the transformations run without any effects. This is because some
    # transformations may modify a url in a way that makes a previous transformation
    # applicable when it wasn't originally, so it will need to be run again.
    while True:
        for cls in UrlTransformer.__subclasses__():
            if not cls.is_applicable(parsed_url):
                continue

            before = parsed_url
            parsed_url = cls.apply_transformation(parsed_url)

            # if the url was changed, break the for loop (effectively restarting it)
            if before != parsed_url:
                # first, check how many times this transformation has caused the loop to
                # restart - if it's 3 or more, it's likely we're in an infinite loop and
                # need to bail out entirely
                restarted_by[cls] += 1
                if restarted_by[cls] >= 3:
                    raise UrlTransformationLoopError

                break
        else:
            # all transformations ran with no changes, can stop working on this url
            break

    return parsed_url


def has_path(parsed_url: ParseResult) -> bool:
    """Whether a parsed url has a path component (and not just a trailing slash)."""
    return parsed_url.path not in ("", "/")


class UrlTransformer(ABC):
    """Abstract base class for url transformers.

    This is a bit of an unusual usage of ABC, since normally it would only cause errors
    when trying to instantiate the subclasses, which will never happen here since the
    methods are classmethods. However, prospector is still able to recognize when the
    abstract method(s) haven't been overridden.
    """

    @classmethod
    def is_applicable(cls, parsed_url: ParseResult) -> bool:
        """Return whether this transformation should be applied to the url.

        This can be used for cases like a transformation that only applies to specific
        domains. If not overridden, the transformation will apply to all urls.
        """
        # pylint: disable=unused-argument
        return True

    @classmethod
    @abstractmethod
    def apply_transformation(cls, parsed_url: ParseResult) -> ParseResult:
        """Apply the actual transformation process to the url.

        Subclass implementations of this method should be idempotent, since a
        transformation may be applied to a particular url any number of times until
        the process completes.
        """
        return parsed_url


class UtmQueryParamRemover(UrlTransformer):
    """Remove any utm_* query parameters from a url."""

    @classmethod
    def apply_transformation(cls, parsed_url: ParseResult) -> ParseResult:
        """Apply the actual transformation process to the url."""
        query_params = parse_qs(parsed_url.query, keep_blank_values=True)

        cleaned_params = {
            param: value
            for param, value in query_params.items()
            if not param.startswith("utm_")
        }

        return parsed_url._replace(query=urlencode(cleaned_params, doseq=True))


class TwitterMobileConverter(UrlTransformer):
    """Convert links to Twitter mobile version to the bare domain."""

    @classmethod
    def is_applicable(cls, parsed_url: ParseResult) -> bool:
        """Return whether this transformation should be applied to the url."""
        return parsed_url.hostname == "mobile.twitter.com"

    @classmethod
    def apply_transformation(cls, parsed_url: ParseResult) -> ParseResult:
        """Apply the actual transformation process to the url."""
        return parsed_url._replace(netloc="twitter.com")


class FacebookTrackingRemover(UrlTransformer):
    """Remove Facebook's "click tracking" query parameter (fbclid)."""

    @classmethod
    def apply_transformation(cls, parsed_url: ParseResult) -> ParseResult:
        """Apply the actual transformation process to the url."""
        query_params = parse_qs(parsed_url.query, keep_blank_values=True)

        query_params.pop("fbclid", None)

        return parsed_url._replace(query=urlencode(query_params, doseq=True))


class RedditTrackingRemover(UrlTransformer):
    """Remove Reddit's "share tracking" query parameters (st and sh)."""

    @classmethod
    def is_applicable(cls, parsed_url: ParseResult) -> bool:
        """Return whether this transformation should be applied to the url."""
        return parsed_url.hostname == "www.reddit.com"

    @classmethod
    def apply_transformation(cls, parsed_url: ParseResult) -> ParseResult:
        """Apply the actual transformation process to the url."""
        query_params = parse_qs(parsed_url.query, keep_blank_values=True)

        query_params.pop("st", None)
        query_params.pop("sh", None)

        return parsed_url._replace(query=urlencode(query_params, doseq=True))


class WikipediaMobileConverter(UrlTransformer):
    """Convert links to Wikipedia mobile version to the standard version."""

    @classmethod
    def is_applicable(cls, parsed_url: ParseResult) -> bool:
        """Return whether this transformation should be applied to the url."""
        return parsed_url.hostname.endswith(".m.wikipedia.org") and has_path(parsed_url)

    @classmethod
    def apply_transformation(cls, parsed_url: ParseResult) -> ParseResult:
        """Apply the actual transformation process to the url."""
        new_domain = parsed_url.hostname.replace(".m.wikipedia.org", ".wikipedia.org")
        return parsed_url._replace(netloc=new_domain)


class YoutubeUnshortener(UrlTransformer):
    """Converts youtu.be links into youtube.com ones."""

    @classmethod
    def is_applicable(cls, parsed_url: ParseResult) -> bool:
        """Return whether this transformation should be applied to the url."""
        return parsed_url.hostname == "youtu.be" and has_path(parsed_url)

    @classmethod
    def apply_transformation(cls, parsed_url: ParseResult) -> ParseResult:
        """Apply the actual transformation process to the url.

        This converts a url like https://youtu.be/asdf to
        https://www.youtube.com/watch?v=asdf (and retains any other query params).
        """
        video_id = parsed_url.path.strip("/")

        # use parse_qsl() and insert() here so the v= is always the first query param
        query_params = parse_qsl(parsed_url.query, keep_blank_values=True)
        query_params.insert(0, ("v", video_id))

        return parsed_url._replace(
            netloc="www.youtube.com", path="/watch", query=urlencode(query_params)
        )
