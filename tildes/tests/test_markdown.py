# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from bs4 import BeautifulSoup

from tildes.enums import HTMLSanitizationContext
from tildes.lib.markdown import convert_markdown_to_safe_html


def test_script_tag_escaped():
    """Ensure that a <script> tag can't get through."""
    markdown = "<script>alert()</script>"
    sanitized = convert_markdown_to_safe_html(markdown)

    assert "<script>" not in sanitized


def test_basic_markdown_unescaped():
    """Test that some common markdown comes through without escaping."""
    markdown = (
        "# Here's a header.\n\n"
        "This chunk of text has **some bold** and *some italics* in it.\n\n"
        "A separator will be below this paragraph.\n\n"
        "---\n\n"
        "* An unordered list item\n"
        "* Another list item\n\n"
        "> This should be a quote.\n\n"
        "    And a code block\n\n"
        "Also some `inline code` and [a link](http://example.com).\n\n"
        "And a manual break  \nbetween lines.\n\n"
    )
    sanitized = convert_markdown_to_safe_html(markdown)

    assert "&lt;" not in sanitized


def test_strikethrough():
    """Ensure strikethrough works and doesn't turn into a group link."""
    markdown = "This ~should not~ should work"
    processed = convert_markdown_to_safe_html(markdown)

    assert "<del>" in processed
    assert "<a" not in processed


def test_table():
    """Ensure table markdown works."""
    markdown = (
        "|Header 1|Header 2|Header 3|\n"
        "|--------|-------:|:------:|\n"
        "|1 - 1   |1 - 2   |1 - 3   |\n"
        "|2 - 1|2 - 2|2 - 3|\n"
    )
    processed = convert_markdown_to_safe_html(markdown)

    assert "<table>" in processed
    assert processed.count("<tr") == 3
    assert processed.count("<td") == 6
    assert 'align="right"' in processed
    assert 'align="center"' in processed


def test_deliberate_ordered_list():
    """Ensure a "deliberate" ordered list works."""
    markdown = (
        "My first line of text.\n\n"
        "1. I want\n"
        "2. An ordered\n"
        "3. List here\n\n"
        "A final line."
    )
    html = convert_markdown_to_safe_html(markdown)

    assert "<ol>" in html


def test_accidental_ordered_list():
    """Ensure a common "accidental" ordered list gets escaped."""
    markdown = "1975. It was a long time ago."
    html = convert_markdown_to_safe_html(markdown)

    assert "<ol" not in html


def test_merged_blockquotes():
    """Ensure subsequent blockquotes are merged."""
    markdown = "> Paragraph 1\n\n> Paragraph 2"
    html = convert_markdown_to_safe_html(markdown)

    assert html.count("<blockquote") == 1


def test_separated_blockquotes():
    """Ensure blockquotes can be separated with an additional newline."""
    markdown = "> Paragraph 1\n\n\n> Paragraph 2"
    html = convert_markdown_to_safe_html(markdown)

    assert html.count("<blockquote") == 2


def test_existing_newline_not_doubled():
    """Ensure that the standard markdown line break doesn't result in two."""
    markdown = "A deliberate line  \nbreak"
    html = convert_markdown_to_safe_html(markdown)

    assert html.count("<br") == 1


def test_newline_creates_br():
    """Ensure that a simple newline inside a paragraph creates a br tag."""
    markdown = "This wouldn't\nnormally work"
    html = convert_markdown_to_safe_html(markdown)

    assert "<br>" in html


def test_multiple_newlines():
    """Ensure markdown with multiple newlines has expected result."""
    lines = ["One.", "Two.", "Three.", "Four.", "Five."]
    markdown = "\n".join(lines)
    html = convert_markdown_to_safe_html(markdown)

    assert html.count("<br") == len(lines) - 1

    assert all(line in html for line in lines)


def test_newline_in_code_block():
    """Ensure newlines in code blocks don't add a <br>."""
    markdown = "```\ndef testing_for_newlines():\n    pass\n```\n"
    html = convert_markdown_to_safe_html(markdown)

    assert "<br" not in html


def test_http_link_linkified():
    """Ensure that writing an http url results in a link."""
    markdown = "I like http://example.com as an example."
    processed = convert_markdown_to_safe_html(markdown)

    assert '<a href="http://example.com">' in processed


def test_https_link_linkified():
    """Ensure that writing an https url results in a link."""
    markdown = "Also, https://example.com should work."
    processed = convert_markdown_to_safe_html(markdown)

    assert '<a href="https://example.com">' in processed


def test_mailto_link_linkified():
    """Ensure that writing an email results in a working mailto link."""
    markdown = "My email is email@example.com."
    processed = convert_markdown_to_safe_html(markdown)

    assert '<a href="mailto:email@example.com">' in processed


def test_link_with_path_linkified():
    """Ensure a link with a path results in a link."""
    markdown = "So http://example.com/a/b_c_d/e too?"
    processed = convert_markdown_to_safe_html(markdown)

    assert '<a href="http://example.com/a/b_c_d/e">' in processed


def test_link_with_query_string_linkified():
    """Ensure a link with a query string results in a link."""
    markdown = "Also http://example.com?something=true&test=yes works?"
    processed = convert_markdown_to_safe_html(markdown)

    assert '<a href="http://example.com?something=true&amp;test=yes">' in processed


def test_other_protocol_urls_not_linkified():
    """Ensure some other protocols don't linkify (not comprehensive)."""
    protocols = ("data", "ftp", "irc", "news", "ssh", "xmpp")

    for protocol in protocols:
        markdown = f"Testing {protocol}://example.com for linking"
        processed = convert_markdown_to_safe_html(markdown)

        assert "href" not in processed


def test_html_attr_whitelist_violation():
    """Ensure non-whitelisted HTML attributes are removed."""
    markdown = (
        '<a href="example.com" title="example" target="_blank" '
        'referrerpolicy="unsafe-url">test link</a>'
    )
    processed = convert_markdown_to_safe_html(markdown)

    assert processed == '<p><a href="example.com" title="example">test link</a></p>\n'


def test_html_lookalike_not_closed():
    """Ensure text that looks like an HTML tag isn't "fixed" by adding a closing tag."""
    markdown = "I can't believe it's not <blank>!"
    processed = convert_markdown_to_safe_html(markdown)

    assert "&lt;blank&gt;" in processed
    assert "&lt;/blank&gt;" not in processed


def test_html_lookalike_closing_not_removed():
    """Ensure text that looks like an HTML close tag isn't removed without an opener."""
    markdown = "Well, that's just great.</sarcasm>"
    processed = convert_markdown_to_safe_html(markdown)

    assert "&lt;/sarcasm&gt;" in processed


def test_a_href_protocol_violation():
    """Ensure link to other protocols removes the link (not comprehensive)."""
    protocols = ("data", "ftp", "irc", "news", "ssh", "xmpp")

    for protocol in protocols:
        markdown = f"Testing [a link]({protocol}://example.com) for linking"
        processed = convert_markdown_to_safe_html(markdown)

        assert "href" not in processed


def test_group_reference_linkified():
    """Ensure a simple group reference gets linkified."""
    markdown = "Yeah, I saw that in ~books.fantasy yesterday."
    processed = convert_markdown_to_safe_html(markdown)

    soup = BeautifulSoup(processed, features="html5lib")
    assert soup.find("a", href="/~books.fantasy")


def test_multiple_group_references_linkified():
    """Ensure multiple group references are all linkified."""
    markdown = (
        "I like to keep an eye on:\n\n"
        "* ~music.metal\n"
        "* ~music.metal.progressive\n"
        "* ~music.post_rock\n"
    )
    processed = convert_markdown_to_safe_html(markdown)

    soup = BeautifulSoup(processed, features="html5lib")
    assert len(soup.find_all("a")) == 3


def test_invalid_group_reference_not_linkified():
    """Ensure an invalid group reference doesn't linkify."""
    markdown = (
        "You can't name a group ~games.pokémon.\n"
        "You also can't have a name like ~_underscores."
    )
    processed = convert_markdown_to_safe_html(markdown)

    assert "<a" not in processed


def test_approximately_tilde_not_linkified():
    """Ensure a tilde in front of a number doesn't linkify."""
    markdown = "Mix in ~2 cups of flour and ~1.5 tbsp of sugar with ~3kg of meat."
    processed = convert_markdown_to_safe_html(markdown)

    assert "<a" not in processed


def test_uppercase_group_ref_links_correctly():
    """Ensure using uppercase in a group ref works but links correctly."""
    markdown = "That was in ~Music.Metal.Progressive"
    processed = convert_markdown_to_safe_html(markdown)

    soup = BeautifulSoup(processed, features="html5lib")
    assert soup.find("a", href="/~music.metal.progressive")


def test_existing_link_group_ref_not_replaced():
    """Ensure a group ref with an existing link doesn't get overwritten."""
    markdown = "Doesn't go [~where.you.expect](http://example.com)"
    processed = convert_markdown_to_safe_html(markdown)

    assert '<a href="http://example.com"' in processed
    assert 'href="/~where.you.expect"' not in processed


def test_group_ref_inside_link_not_replaced():
    """Ensure a group ref inside a longer link doesn't get re-linked."""
    markdown = "Found [this band from a ~music.punk post](http://whitelung.ca)"
    processed = convert_markdown_to_safe_html(markdown)

    assert processed.count("<a") == 1
    assert 'href="/~music.punk"' not in processed


def test_group_ref_inside_pre_ignored():
    """Ensure a group ref inside a <pre> tag doesn't get linked."""
    markdown = (
        "```\n"
        "# This is a code block\n"
        "# I found this code on ~comp.lang.python\n"
        "```\n"
    )
    processed = convert_markdown_to_safe_html(markdown)

    assert "<a" not in processed


def test_group_ref_inside_other_tags_linkified():
    """Ensure a group ref inside non-ignored tags gets linked."""
    markdown = "> Here is **a ~group.reference inside** other stuff"
    processed = convert_markdown_to_safe_html(markdown)

    soup = BeautifulSoup(processed, features="html5lib")
    assert soup.find("a", href="/~group.reference")


def test_username_reference_linkified():
    """Ensure a basic username reference gets linkified."""
    markdown = "Hey @SomeUser, what do you think of this?"
    processed = convert_markdown_to_safe_html(markdown)

    soup = BeautifulSoup(processed, features="html5lib")
    assert soup.find("a", href="/user/SomeUser")


def test_u_style_username_ref_linked():
    """Ensure a /u/username reference gets linkified."""
    markdown = "Hey /u/SomeUser, what do you think of this?"
    processed = convert_markdown_to_safe_html(markdown)

    soup = BeautifulSoup(processed, features="html5lib")
    assert soup.find("a", href="/user/SomeUser")


def test_u_alt_style_username_ref_linked():
    """Ensure a u/username reference gets linkified."""
    markdown = "Hey u/SomeUser, what do you think of this?"
    processed = convert_markdown_to_safe_html(markdown)

    soup = BeautifulSoup(processed, features="html5lib")
    assert soup.find("a", href="/user/SomeUser")


def test_accidental_u_alt_style_not_linked():
    """Ensure an "accidental" u/ usage won't get linked."""
    markdown = "I think those are caribou/reindeer."
    processed = convert_markdown_to_safe_html(markdown)

    assert "<a" not in processed


def test_username_and_group_refs_linked():
    """Ensure username and group references together get linkified."""
    markdown = "@SomeUser makes the best posts in ~some.group for sure"
    processed = convert_markdown_to_safe_html(markdown)

    soup = BeautifulSoup(processed, features="html5lib")
    assert soup.find("a", href="/user/SomeUser")
    assert soup.find("a", href="/~some.group")


def test_invalid_username_not_linkified():
    """Ensure an invalid username doesn't get linkified."""
    markdown = "You can't register a username like @_underscores_"
    processed = convert_markdown_to_safe_html(markdown)

    assert "<a" not in processed


def test_username_ref_inside_pre_ignored():
    """Ensure a username ref inside a <pre> tag doesn't get linked."""
    markdown = "```\n# Code blatantly stolen from @HelpfulGuy on StackOverflow\n```\n"
    processed = convert_markdown_to_safe_html(markdown)

    assert "<a" not in processed


def test_group_ref_inside_code_ignored():
    """Ensure a group reference inside a <code> tag doesn't get linked."""
    markdown = "Strikethrough works like: `this ~should not~ work`."
    processed = convert_markdown_to_safe_html(markdown)

    assert "<a" not in processed


def test_image_syntax_ignored():
    """Ensure inline image syntax is treated as a link."""
    markdown = "An exclamation mark preceding a ![link](url)."
    processed = convert_markdown_to_safe_html(markdown)

    assert "!<a" in processed
    assert "img" not in processed


def test_a_rel_removed_default_context():
    """Ensure a rel= attr is removed from an <a> tag by default."""
    markdown = '<a href="http://example.com" rel="something">Link</a>'
    processed = convert_markdown_to_safe_html(markdown)

    assert "rel=" not in processed


def test_a_rel_kept_user_bio_context():
    """Ensure a rel= attr is kept on an <a> tag in the user bio context."""
    markdown = '<a href="http://example.com" rel="something">Link</a>'
    processed = convert_markdown_to_safe_html(
        markdown, HTMLSanitizationContext.USER_BIO
    )

    assert "rel=" in processed
