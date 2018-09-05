# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from tildes.lib.string import (
    convert_to_url_slug,
    truncate_string,
    truncate_string_at_char,
    word_count,
)


def test_simple_truncate():
    """Ensure a simple truncation by length works correctly."""
    truncated = truncate_string("123456789", 5, overflow_str=None)
    assert truncated == "12345"


def test_simple_truncate_with_overflow():
    """Ensure a simple truncation by length with an overflow string works."""
    truncated = truncate_string("123456789", 5)
    assert truncated == "12..."


def test_truncate_same_length():
    """Ensure truncation doesn't happen if the string is the desired length."""
    original = "123456789"
    assert truncate_string(original, len(original)) == original


def test_truncate_at_char():
    """Ensure truncation at a particular character works."""
    original = "asdf zxcv"
    assert truncate_string_at_char(original, " ") == "asdf"


def test_truncate_at_last_char():
    """Ensure truncation happens at the last occurrence of the character."""
    original = "as df zx cv"
    assert truncate_string_at_char(original, " ") == "as df zx"


def test_truncate_at_nonexistent_char():
    """Ensure truncation-at-character doesn't apply if char isn't present."""
    original = "asdfzxcv"
    assert truncate_string_at_char(original, " ") == original


def test_truncate_at_multiple_chars():
    """Ensure truncation with multiple characters uses the rightmost one."""
    original = "as-df=zx_cv"
    assert truncate_string_at_char(original, "-=") == "as-df"


def test_truncate_length_and_char():
    """Ensure combined length+char truncation works as expected."""
    original = "12345-67890-12345"
    truncated = truncate_string(original, 8, truncate_at_chars="-", overflow_str=None)
    assert truncated == "12345"


def test_truncate_length_and_nonexistent_char():
    """Ensure length+char truncation works if the char isn't present."""
    original = "1234567890-12345"
    truncated = truncate_string(original, 8, truncate_at_chars="-", overflow_str=None)
    assert truncated == "12345678"


def test_simple_url_slug_conversion():
    """Ensure that a simple url slug conversion works as expected."""
    assert convert_to_url_slug("A Simple Test") == "a_simple_test"


def test_url_slug_with_punctuation():
    """Ensure url slug conversion with punctuation works as expected."""
    original = "Here's a string. It has (some) punctuation!"
    expected = "heres_a_string_it_has_some_punctuation"
    assert convert_to_url_slug(original) == expected


def test_url_slug_with_apostrophes():
    """Ensure url slugs don't replace apostrophes with underscores."""
    original = "Here's what we don’t want as underscores"
    expected = "heres_what_we_dont_want_as_underscores"
    assert convert_to_url_slug(original) == expected


def test_url_slug_truncation():
    """Ensure a simple url slug truncates as expected."""
    original = "Here's another string to truncate."
    assert convert_to_url_slug(original, 15) == "heres_another"


def test_multibyte_url_slug():
    """Ensure converting/truncating a slug with encoded characters works."""
    original = "Python ist eine üblicherweise höhere Programmiersprache"
    expected = "python_ist_eine_%C3%BCblicherweise"
    assert convert_to_url_slug(original, 45) == expected


def test_multibyte_conservative_truncation():
    """Ensure truncating a multibyte url slug won't massively shorten it."""
    # this string has a comma as the 6th char which will be converted to an underscore,
    # so if truncation amount isn't restricted, it would result in a 46-char slug
    # instead of the full 100.
    original = "パイソンは、汎用のプログラミング言語である"
    assert len(convert_to_url_slug(original, 100)) == 100


def test_multibyte_whole_character_truncation():
    """Ensure truncation happens at the edge of a multibyte character."""
    # each of these characters url-encodes to 3 bytes = 9 characters each, so only the
    # first character should be included for all lengths from 9 - 17
    original = "コード"
    for limit in range(9, 18):
        assert convert_to_url_slug(original, limit) == "%E3%82%B3"


def test_simple_word_count():
    """Ensure word-counting a simple string works as expected."""
    string = "Here is a simple string of words, nothing fancy."
    assert word_count(string) == 9


def test_word_count_with_apostrophes():
    """Ensure apostrophes don't mess up the word count."""
    string = "It's not always false that apostrophes aren't counted properly."
    assert word_count(string) == 9


def test_word_count_with_curly_apostrophes():
    """Ensure curly apostrophes don't mess up the word count."""
    string = "It’s not always false that apostrophes aren’t counted properly."
    assert word_count(string) == 9


def test_word_count_with_lots_of_punctuation():
    """Ensure word count works properly with lots of punctuation."""
    string = (
        'Even if "everyone" knows this should still work with a lot '
        "-- a LOT -- of punctuation (or spécial characters), it's probably "
        "best not to count 100% on it; that's just foolish/risky."
    )
    assert word_count(string) == 31
