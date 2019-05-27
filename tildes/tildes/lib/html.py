# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions related to HTML parsing/modification."""

from bs4 import BeautifulSoup

from tildes.lib.string import convert_to_url_slug


def add_anchors_to_headings(html: str) -> str:
    """Replace all heading elements with ones with ids that link to themselves."""
    soup = BeautifulSoup(html, features="html5lib")

    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

    for heading in headings:
        # generate an anchor from the string contents of the heading
        anchor = convert_to_url_slug("".join([string for string in heading.strings]))

        # create a link to that anchor, and put the heading's contents inside it
        link = soup.new_tag("a", href=f"#{anchor}")
        link.contents = heading.contents

        # put that link in a replacement same-level heading with the anchor as id
        new_heading = soup.new_tag(heading.name, id=anchor)
        new_heading.append(link)

        heading.replace_with(new_heading)

    # html5lib adds <html> and <body> tags around the fragment, strip them back out
    return "".join([str(tag) for tag in soup.body.children])
