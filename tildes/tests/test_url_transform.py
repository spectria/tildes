# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from tildes.lib.url_transform import apply_url_transformations


def test_remove_utm_query_params():
    """Ensure that utm query params are removed but others are left."""
    url = "http://example.com/path?utm_source=tildes&utm_campaign=test&something=ok"
    cleaned_url = apply_url_transformations(url)

    assert cleaned_url == "http://example.com/path?something=ok"


def test_non_utm_params_unaffected():
    """Ensure that non-utm_ query params aren't removed."""
    url = "http://example.com/path?one=x&two=y&three=z"
    cleaned_url = apply_url_transformations(url)

    assert cleaned_url == url
