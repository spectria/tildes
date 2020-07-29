# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from tidylib import tidy_document


def test_homepage_tidy_loggedout(webtest_loggedout):
    """Validate HTML5 using Tidy on the Tildes homepage, logged out."""
    homepage = webtest_loggedout.get("/")
    _document, errors = tidy_document(homepage.body)

    assert not errors


def test_homepage_tidy_loggedin(webtest):
    """Validate HTML5 using Tidy on the Tildes homepage, logged in."""
    homepage = webtest.get("/")
    _document, errors = tidy_document(homepage.body)

    assert not errors
