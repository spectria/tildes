# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions/constants related to markdown handling."""

import re
from functools import partial
from typing import Any, Callable, Iterator, List, Match, Optional, Pattern, Tuple

import bleach
from bs4 import BeautifulSoup
from html5lib.filters.base import Filter
from html5lib.treewalkers.base import NonRecursiveTreeWalker
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, PhpLexer
from pygments.util import ClassNotFound

from tildes.enums import HTMLSanitizationContext
from tildes.metrics import histogram_timer
from tildes.schemas.group import is_valid_group_path
from tildes.schemas.user import is_valid_username

from .cmark import (
    CMARK_EXTENSIONS,
    cmark_find_syntax_extension,
    cmark_node_free,
    CMARK_OPTS,
    cmark_parser_attach_syntax_extension,
    cmark_parser_feed,
    cmark_parser_finish,
    cmark_parser_free,
    cmark_parser_get_syntax_extensions,
    cmark_parser_new,
    cmark_render_html,
)


def allow_syntax_highlighting_classes(tag: str, name: str, value: str) -> bool:
    """Allow all CSS classes from Pygments.

    Pygments will add a <code class="highlight">, as well as many <span> tags around
    elements of the code, with classes all starting with "syntax-".
    """
    if tag not in ("span", "code"):
        raise ValueError("This method only sanitizes <span> and <code> tags")

    if tag == "span":
        # allow class attribute with a single class starting with "syntax-"
        return name == "class" and " " not in value and value.startswith("syntax-")

    if tag == "code":
        # allow class attribute with a single class of exactly "highlight"
        return name == "class" and value == "highlight"

    return False


HTML_TAG_WHITELIST = (
    "a",
    "b",
    "blockquote",
    "br",
    "code",
    "del",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "ins",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "sub",
    "sup",
    "span",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
)
PROTOCOL_WHITELIST = ("http", "https", "mailto")

HTML_ATTRIBUTE_WHITELIST_DEFAULT = {
    "a": ["href", "title"],
    "ol": ["start"],
    "td": ["align"],
    "th": ["align"],
    "code": allow_syntax_highlighting_classes,
    "span": allow_syntax_highlighting_classes,
}

# per-context overrides for allowed attributes
HTML_ATTRIBUTE_WHITELIST_OVERRIDES = {
    HTMLSanitizationContext.USER_BIO: {"a": ["href", "title", "rel"]}
}

# Regex that finds ordered list markdown that was probably accidental - ones being
# initiated by anything except "1." at the start of a post
BAD_ORDERED_LIST_REGEX = re.compile(
    r"((?:\A)"  # The start of the entire text
    r"(?!1\.)\d+)"  # A number that isn't "1"
    r"\.\s"  # Followed by a period and a space
)

STRIP_IMAGE_ELEMENTS_REGEX = re.compile(r'<img src="([^"<>]*?)" alt="([^"<>]*?)" />')

SUBSEQUENT_BLOCKQUOTES_REGEX = re.compile("^>([^\n]*?)\n\n(?=>)", flags=re.MULTILINE)


@histogram_timer("markdown_processing")
def convert_markdown_to_safe_html(
    markdown: str, context: Optional[HTMLSanitizationContext] = None
) -> str:
    """Convert markdown to sanitized HTML."""
    # apply custom pre-processing to markdown
    markdown = preprocess_markdown(markdown)

    markdown_bytes = markdown.encode("utf8")

    parser = cmark_parser_new(CMARK_OPTS)
    for name in CMARK_EXTENSIONS:
        ext = cmark_find_syntax_extension(name)
        cmark_parser_attach_syntax_extension(parser, ext)
    exts = cmark_parser_get_syntax_extensions(parser)

    cmark_parser_feed(parser, markdown_bytes, len(markdown_bytes))
    doc = cmark_parser_finish(parser)

    html_bytes = cmark_render_html(doc, CMARK_OPTS, exts)

    cmark_parser_free(parser)
    cmark_node_free(doc)

    html = html_bytes.decode("utf8")

    # apply custom post-processing to HTML
    html = postprocess_markdown_html(html)

    # add linkification and sanitize the final HTML before returning it
    return linkify_and_sanitize_html(html, context)


def preprocess_markdown(markdown: str) -> str:
    """Pre-process markdown before passing it to CommonMark."""
    markdown = escape_accidental_ordered_lists(markdown)

    markdown = merge_subsequent_blockquotes(markdown)

    # fix the "shrug" emoji ¯\_(ツ)_/¯ to prevent markdown mangling it
    markdown = markdown.replace(r"¯\_(ツ)_/¯", r"¯\\\_(ツ)\_/¯")

    return markdown


def merge_subsequent_blockquotes(markdown: str) -> str:
    """Merge subsequent (separated) blockquotes into a single one.

    By default, if someone quotes more than one paragraph without also adding the >
    symbol on the blank lines between them, they will be interpreted as separate
    blockquotes. This almost never seems to be intended, so this merges them. If
    separate quotes are wanted, they can still achieve it by using at least two
    newlines between quoted paragraphs (or various other methods).
    """
    return SUBSEQUENT_BLOCKQUOTES_REGEX.sub(">\\1\n>\n", markdown)


def escape_accidental_ordered_lists(markdown: str) -> str:
    """Escape markdown that's probably an accidental ordered list.

    It's a common markdown mistake to accidentally start a numbered list, by beginning a
    post with a number followed by a period. For example, someone might try to write
    "1975. It was a long time ago.", and the result will be a comment that says "1. It
    was a long time ago." since that gets parsed into a numbered list.

    This fixes that quirk of markdown by escaping anything that would start a numbered
    list at the beginning of a post, except for "1. ".
    """
    return BAD_ORDERED_LIST_REGEX.sub(r"\1\\. ", markdown)


def postprocess_markdown_html(html: str) -> str:
    """Apply post-processing to HTML generated by markdown parser."""
    # cmark (and cmark-gfm) replaces double-quote characters with the &quot; entity.
    # This is almost always unnecessary, and is causing issues with some of the HTML
    # processing, since (for example) BeautifulSoup will convert them back, which causes
    # the string-replacement in apply_syntax_highlighting() to fail if a code block
    # contains any double-quote characters.
    #
    # We'll just do a full replacement here - this has a possibility of being dangerous,
    # but it should be extremely unlikely and the sanitization function should make sure
    # that nothing malicious can happen regardless.
    html = html.replace("&quot;", '"')

    # apply syntax highlighting to code blocks
    html = apply_syntax_highlighting(html)

    # replace <img> elements that were generated by `![ ]( )` Markdown syntax
    html = strip_image_elements(html)

    return html


class CodeHtmlFormatter(HtmlFormatter):
    """Custom Pygments HtmlFormatter to use a <code> tag.

    The default HtmlFormatter in Pygments outputs the code inside a
    <div class="highlight"><pre>...</pre></div> structure. This changes that to
    <code class="highlight">...</code> instead (assumes a <pre> is already present).
    """

    def wrap(self, source: Any, outfile: Any) -> Iterator[Tuple[int, str]]:
        """Wrap the highlighted tokens with the <code> tag."""
        # pylint: disable=unused-argument
        yield (0, '<code class="highlight">')
        yield from source
        yield (0, "</code>")


def apply_syntax_highlighting(html: str) -> str:
    """Get all code blocks with defined info string in class and highlight them."""
    soup = BeautifulSoup(html, features="html5lib")

    # Get all code blocks and for every code block that has info string
    code_blocks = soup.find_all("code", class_=re.compile("^language-"))
    for code_block in code_blocks:
        language = code_block["class"][0].replace("language-", "")

        try:
            lexer = get_lexer_by_name(language)
            # If target language is PHP, override default lexer construction
            # and set startinline to True, so even code that is not enclosed
            # inside <?php ... ?> will get highlighted.
            if isinstance(lexer, PhpLexer):
                lexer = PhpLexer(startinline=True)
        except ClassNotFound:
            continue

        highlighted = highlight(
            code_block.text, lexer, CodeHtmlFormatter(classprefix="syntax-")
        )
        html = html.replace(str(code_block), highlighted, 1)

    return html


def strip_image_elements(html: str) -> str:
    """Replace all <img> elements generated from Markdown with <a>.

    The Markdown syntax `![alt text](/url)` creates an image tag. Except for the leading
    `!`, the syntax is identical to that of links. We can pretend we never parsed it as
    a Markdown image by replacing all image tags with links.

        <img src="/url" alt="alt text" />
            ==>
        !<a href="/url">alt text</a>
    """
    return STRIP_IMAGE_ELEMENTS_REGEX.sub(r'!<a href="\1">\2</a>', html)


class LinkifyFilter(Filter):
    """html5lib Filter to convert custom text patterns to links.

    This replaces references to group paths and usernames with links to the relevant
    pages.

    This implementation is based heavily on the linkify implementation from the Bleach
    library.
    """

    # Regex that finds probable references to groups. This isn't "perfect", just a first
    # pass to find likely candidates. The validity of the group path is checked more
    # carefully later.
    # Note: currently specifically excludes paths immediately followed by a tilde, but
    # this may be possible to remove once strikethrough is implemented (since that's
    # probably what they were trying to do)
    GROUP_REFERENCE_REGEX = re.compile(r"(?<!\w)~([\w.]+)\b(?!~)")

    # Regex that finds probable references to users. As above, this isn't "perfect"
    # either but works as an initial pass with the validity of the username checked more
    # carefully later.
    USERNAME_REFERENCE_REGEX = re.compile(r"(?<!\w)(?:/?u/|@)([\w-]+)\b")

    def __init__(
        self, source: NonRecursiveTreeWalker, skip_tags: Optional[List[str]] = None
    ):
        """Initialize a linkification filter to apply to HTML.

        The skip_tags argument can be a list of tag names, and the contents of any of
        those tags will be excluded from linkification.
        """
        super().__init__(source)
        self.skip_tags = skip_tags or []

        # always skip the contents of <a> tags in addition to any others
        self.skip_tags.append("a")

    def __iter__(self) -> Iterator[dict]:
        """Iterate over the tree, modifying it as necessary before yielding."""
        inside_skipped_tags = []

        for token in super().__iter__():
            if (
                token["type"] in ("StartTag", "EmptyTag")
                and token["name"] in self.skip_tags
            ):
                # if this is the start of a tag we want to skip, add it to the list of
                # skipped tags that we're currently inside
                inside_skipped_tags.append(token["name"])
            elif inside_skipped_tags:
                # if we're currently inside any skipped tags, the only thing we want to
                # do is look for all the end tags we need to be able to finish skipping
                if token["type"] == "EndTag":
                    try:
                        inside_skipped_tags.remove(token["name"])
                    except ValueError:
                        pass
            elif token["type"] == "Characters":
                # this is only reachable if inside_skipped_tags is empty, so this is a
                # text token not inside a skipped tag - do the actual linkification
                # replacements

                # Note: doing the two replacements "iteratively" like this only works
                # because they are "disjoint" and we know they're not competing to
                # replace the same text. If more replacements are added in the future
                # that might conflict with each other, this will need to be reworked
                # somehow.
                replaced_tokens = self._linkify_tokens(
                    [token],
                    filter_regex=self.GROUP_REFERENCE_REGEX,
                    linkify_function=self._tokenize_group_match,
                )
                replaced_tokens = self._linkify_tokens(
                    replaced_tokens,
                    filter_regex=self.USERNAME_REFERENCE_REGEX,
                    linkify_function=self._tokenize_username_match,
                )

                # yield all the tokens returned from the replacement process (will be
                # just the original token if nothing was replaced)
                for new_token in replaced_tokens:
                    yield new_token

                # we either yielded new tokens or the original one already, so we don't
                # want to fall through and yield the original again
                continue

            yield token

    @staticmethod
    def _linkify_tokens(
        tokens: List[dict], filter_regex: Pattern, linkify_function: Callable
    ) -> List[dict]:
        """Check tokens for text that matches a regex and linkify it.

        The `filter_regex` argument should be a compiled pattern that will be applied to
        the text in all of the supplied tokens. If any matches are found, they will each
        be used to call `linkify_function`, which will validate the match and convert it
        back into tokens (representing an <a> tag if it is valid for linkifying, or just
        text if not).
        """
        new_tokens = []

        for token in tokens:
            # we don't want to touch any tokens other than character ones
            if token["type"] != "Characters":
                new_tokens.append(token)
                continue

            original_text = token["data"]
            current_index = 0

            for match in filter_regex.finditer(original_text):
                # if there were some characters between the previous match and this one,
                # add a token containing those first
                if match.start() > current_index:
                    new_tokens.append(
                        {
                            "type": "Characters",
                            "data": original_text[current_index : match.start()],
                        }
                    )

                # call the linkify function to convert this match into tokens
                linkified_tokens = linkify_function(match)
                new_tokens.extend(linkified_tokens)

                # move the progress marker up to the end of this match
                current_index = match.end()

            # if there's still some text left over, add one more token for it (this will
            # be the entire thing if there weren't any matches)
            if current_index < len(original_text):
                new_tokens.append(
                    {"type": "Characters", "data": original_text[current_index:]}
                )

        return new_tokens

    @staticmethod
    def _tokenize_group_match(match: Match) -> List[dict]:
        """Convert a potential group reference into HTML tokens."""
        # convert the potential group path to lowercase to allow people to use incorrect
        # casing but still have it link properly
        group_path = match[1].lower()

        # Even though they're technically valid paths, we don't want to linkify anything
        # starting with a number like "~10" or "~4.5", since that's just going to be
        # someone using it in the "approximately" sense. This will be a problem if a
        # top-level group's name ever starts with a number, but I think that's unlikely.
        is_ignored = group_path.startswith(tuple("0123456789"))

        # if it's a valid group path and not ignored by the above logic, convert to <a>
        if is_valid_group_path(group_path) and not is_ignored:
            return [
                {
                    "type": "StartTag",
                    "name": "a",
                    "data": {
                        (None, "class"): "link-group",
                        (None, "href"): f"/~{group_path}",
                    },
                },
                {"type": "Characters", "data": match[0]},
                {"type": "EndTag", "name": "a"},
            ]

        # one of the checks failed, so just keep it as the original text
        return [{"type": "Characters", "data": match[0]}]

    @staticmethod
    def _tokenize_username_match(match: Match) -> List[dict]:
        """Convert a potential username reference into HTML tokens."""
        # if it's a valid username, convert to <a>
        if is_valid_username(match[1]):
            return [
                {
                    "type": "StartTag",
                    "name": "a",
                    "data": {
                        (None, "class"): "link-user",
                        (None, "href"): f"/user/{match[1]}",
                    },
                },
                {"type": "Characters", "data": match[0]},
                {"type": "EndTag", "name": "a"},
            ]

        # the username wasn't valid, so just keep it as the original text
        return [{"type": "Characters", "data": match[0]}]


def linkify_and_sanitize_html(
    html: str, context: Optional[HTMLSanitizationContext] = None
) -> str:
    """Use bleach and html5lib filters to linkify and sanitize HTML."""
    # list of tag names to exclude from linkification
    linkify_skipped_tags = ["code", "pre"]

    tildes_linkifier = partial(LinkifyFilter, skip_tags=linkify_skipped_tags)

    attribute_whitelist = HTML_ATTRIBUTE_WHITELIST_DEFAULT
    if context:
        # include overrides for the current context
        overrides = HTML_ATTRIBUTE_WHITELIST_OVERRIDES.get(context, {})
        attribute_whitelist = {**attribute_whitelist, **overrides}

    cleaner = bleach.Cleaner(
        tags=HTML_TAG_WHITELIST,
        attributes=attribute_whitelist,
        protocols=PROTOCOL_WHITELIST,
        filters=[tildes_linkifier],
    )
    return cleaner.clean(html)
