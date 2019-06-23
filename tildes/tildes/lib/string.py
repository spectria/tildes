# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions related to processing/manipulating strings."""

import re
import unicodedata
from typing import Iterator, List, Optional
from urllib.parse import quote
from xml.etree.ElementTree import Element

from html5lib import HTMLParser


# regex for matching an entire word, handles words that include an apostrophe
WORD_REGEX = re.compile(r"\w[\w'’]*")


def word_count(string: str) -> int:
    """Count the number of words in the string."""
    return len(WORD_REGEX.findall(string))


def convert_to_url_slug(original: str, max_length: int = 100) -> str:
    """Convert a string (often a title) into one usable as a url slug."""
    slug = original.lower()

    # remove apostrophes so contractions don't get broken up by underscores
    slug = re.sub("['’]", "", slug)

    # replace all remaining non-word characters with underscores
    slug = re.sub(r"\W+", "_", slug)

    # remove any consecutive underscores
    slug = re.sub("_{2,}", "_", slug)

    # remove "hanging" underscores on the start and/or end
    slug = slug.strip("_")

    # url-encode the slug
    encoded_slug = quote(slug)

    # if the slug's already short enough, just return without worrying about how it will
    # need to be truncated
    if len(encoded_slug) <= max_length:
        return encoded_slug

    # Truncating a url-encoded slug can be tricky if there are any multi-byte unicode
    # characters, since the %-encoded forms of them can be quite long. Check to see if
    # the slug looks like it might contain any of those.
    maybe_multi_bytes = bool(re.search("%..%", encoded_slug))

    # if that matched, we need to take a more complicated approach
    if maybe_multi_bytes:
        return _truncate_multibyte_slug(slug, max_length)

    # simple truncate - break at underscore if possible, no overflow string
    return truncate_string(
        encoded_slug, max_length, truncate_at_chars="_", overflow_str=None
    )


def _truncate_multibyte_slug(original: str, max_length: int) -> str:
    """URL-encode and truncate a slug known to contain multi-byte chars."""
    # instead of the normal method of truncating "backwards" from the end of the string,
    # build it up one encoded character at a time from the start until it's too long
    encoded_slug = ""
    for character in original:
        encoded_char = quote(character)

        # if adding this onto the string would make it too long, stop here
        if len(encoded_slug) + len(encoded_char) > max_length:
            break

        encoded_slug += encoded_char

    # Now we know that the string is made up of "whole" characters and is close to the
    # maximum length. We'd still like to truncate it at an underscore if possible, but
    # some languages like Japanese and Chinese won't have many (or any) underscores in
    # the slug, and we could end up losing a lot of the characters. So try breaking it
    # at an underscore, but if it means more than 30% of the slug gets cut off, just
    # leave it alone. This means that some url slugs in other languages will end in
    # partial words, but determining the word edges is not simple.
    acceptable_truncation = 0.7

    truncated_slug = truncate_string_at_char(encoded_slug, "_")

    if len(truncated_slug) / len(encoded_slug) >= acceptable_truncation:
        return truncated_slug

    return encoded_slug


def truncate_string(
    original: str,
    length: int,
    truncate_at_chars: Optional[str] = None,
    overflow_str: Optional[str] = "...",
) -> str:
    """Truncate a string to be no longer than a specified length.

    If `truncate_at_chars` is specified (as a string, one or more characters), the
    truncation will happen at the last occurrence of any of those chars inside the
    remaining string after it has been initially cut down to the desired length.

    `overflow_str` will be appended to the result, and its length is included in the
    final string length. So for example, if `overflow_str` has a length of 3 and the
    target length is 10, at most 7 characters of the original string will be kept.
    """
    if overflow_str is None:
        overflow_str = ""

    # no need to do anything if the string is already short enough
    if len(original) <= length:
        return original

    # cut the string down to the max desired length (leaving space for the overflow
    # string if one is specified)
    truncated = original[: length - len(overflow_str)]

    # if we don't want to truncate at particular characters, we're done
    if not truncate_at_chars:
        return truncated + overflow_str

    # break the string at one of the requested chars instead, if possible
    truncated = truncate_string_at_char(truncated, truncate_at_chars)

    return truncated + overflow_str


def truncate_string_at_char(original: str, valid_chars: str) -> str:
    """Truncate a string at the last occurrence of a particular character.

    Supports passing multiple valid characters (as a string) for `valid_chars`, for
    example valid_chars='.?!' would truncate at the "right-most" occurrence of any of
    those 3 characters in the string.
    """
    # work backwards through the string until we find one of the chars we want
    for num_from_end, char in enumerate(reversed(original), start=1):
        if char in valid_chars:
            break
    else:
        # the loop didn't break, so we looked through the entire string and didn't find
        # any of the desired characters - can't do anything
        return original

    # a truncation char was found, so -num_from_end is the position to stop at
    # pylint: disable=undefined-loop-variable
    return original[:-num_from_end]


def simplify_string(original: str) -> str:
    """Sanitize a string for usage in places where we need a "simple" one.

    This function is useful for sanitizing strings so that they're suitable to be used
    in places like topic titles, message subjects, and so on.

    Strings processed by this function:

    * have unicode chars from the "separator" category replaced with spaces
    * have unicode chars from the "other" category stripped out, except for newlines,
      which are replaced with spaces
    * have leading and trailing whitespace removed
    * have multiple consecutive spaces collapsed into a single space
    """
    simplified = _sanitize_characters(original)

    # replace consecutive spaces with a single space
    simplified = re.sub(r"\s{2,}", " ", simplified)

    # remove any remaining leading/trailing whitespace
    simplified = simplified.strip()

    return simplified


def _sanitize_characters(original: str) -> str:
    """Process a string and filter/replace problematic unicode."""
    final_characters = []

    for char in original:
        category = unicodedata.category(char)

        if category.startswith("Z"):
            # "separator" chars - replace with a normal space
            final_characters.append(" ")
        elif category.startswith("C"):
            # "other" chars (control, formatting, etc.) - filter them out except for
            # newlines, which are replaced with normal spaces
            if char == "\n":
                final_characters.append(" ")
        else:
            # any other type of character, just keep it
            final_characters.append(char)

    return "".join(final_characters)


def separate_string(original: str, separator: str, segment_size: int) -> str:
    """Separate a string into "segments", inserting a separator every X chars.

    This is useful for strings being used as "codes" such as invite codes and 2FA backup
    codes, so that they can be displayed in a more easily-readable format.
    """
    separated = ""

    for count, char in enumerate(original):
        if count > 0 and count % segment_size == 0:
            separated += separator

        separated += char

    return separated


def extract_text_from_html(html: str, skip_tags: Optional[List[str]] = None) -> str:
    """Extract plain text content from the elements inside an HTML string."""

    def extract_text(element: Element, skip_tags: List[str]) -> Iterator[str]:
        """Extract text recursively from elements, optionally skipping some tags.

        This function is Python's xml.etree.ElementTree.Element.itertext() but with the
        added ability to skip over particular tags and not include the text from inside
        them or any of their children.
        """
        if not isinstance(element.tag, str) and element.tag is not None:
            return

        if element.tag in skip_tags:
            return

        if element.text:
            yield element.text

        for subelement in element:
            yield from extract_text(subelement, skip_tags)

            if subelement.tail:
                yield subelement.tail

    skip_tags = skip_tags or []

    html_tree = HTMLParser(namespaceHTMLElements=False).parseFragment(html)

    # extract the text from all of the HTML elements
    extracted_text = "".join([text for text in extract_text(html_tree, skip_tags)])

    # sanitize unicode, remove leading/trailing whitespace, etc.
    return simplify_string(extracted_text)
