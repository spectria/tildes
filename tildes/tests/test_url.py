# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from pytest import raises

from tildes.lib.url import get_domain_from_url


def test_simple_get_domain():
    """Ensure getting the domain from a normal URL works."""
    url = "http://example.com/some/path?query=param&query2=val2"
    assert get_domain_from_url(url) == "example.com"


def test_get_domain_non_url():
    """Ensure attempting to get the domain for a non-url is an error."""
    url = "this is not a url"
    with raises(ValueError):
        get_domain_from_url(url)


def test_get_domain_no_scheme():
    """Ensure getting domain on a url with no scheme is an error."""
    with raises(ValueError):
        get_domain_from_url("example.com/something")


def test_get_domain_explicit_no_scheme():
    """Ensure getting domain works if url is explicit about lack of scheme."""
    assert get_domain_from_url("//example.com/something") == "example.com"


def test_get_domain_strip_www():
    """Ensure stripping the "www." from the domain works as expected."""
    url = "http://www.example.com/a/path/to/something"
    assert get_domain_from_url(url) == "example.com"


def test_get_domain_no_strip_www():
    """Ensure stripping the "www." can be disabled."""
    url = "http://www.example.com/a/path/to/something"
    assert get_domain_from_url(url, strip_www=False) == "www.example.com"


def test_get_domain_subdomain_not_stripped():
    """Ensure a non-www subdomain isn't stripped."""
    url = "http://something.example.com/path/x/y/z"
    assert get_domain_from_url(url) == "something.example.com"
