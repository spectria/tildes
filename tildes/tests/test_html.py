# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from bs4 import BeautifulSoup

from tildes.lib.html import add_anchors_to_headings
from tildes.lib.markdown import convert_markdown_to_safe_html


def test_add_anchor_to_headings():
    """Ensure that a basic heading ends up with the expected id."""
    markdown = "# Some heading"
    html = convert_markdown_to_safe_html(markdown)
    html = add_anchors_to_headings(html)

    assert 'id="some_heading"' in html


def test_anchor_on_complex_heading():
    """Ensure that a more complex heading still gets the expected id."""
    markdown = "# This *heading* has **more formatting**"
    html = convert_markdown_to_safe_html(markdown)
    html = add_anchors_to_headings(html)

    assert 'id="this_heading_has_more_formatting"' in html


def test_heading_links_to_itself():
    """Ensure that a heading ends up containing a link to itself."""
    markdown = "## Important information"
    html = convert_markdown_to_safe_html(markdown)
    html = add_anchors_to_headings(html)

    soup = BeautifulSoup(html, features="html5lib")
    assert soup.h2.a["href"] == "#" + soup.h2["id"]
