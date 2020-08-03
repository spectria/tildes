# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

import subprocess

from pytest import mark


# marks all tests in this module with "html_validation" marker
pytestmark = mark.html_validation


def test_homepage_html_loggedout(webtest_loggedout):
    """Validate HTML5 on the Tildes homepage, logged out."""
    homepage = webtest_loggedout.get("/")
    _run_html5validator(homepage.body)


def test_homepage_html_loggedin(webtest):
    """Validate HTML5 on the Tildes homepage, logged in."""
    homepage = webtest.get("/")
    _run_html5validator(homepage.body)


def _run_html5validator(html):
    """Raises CalledProcessError on validation error."""
    result = subprocess.run(["html5validator", "-"], input=html)
    result.check_returncode()
