# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later


def test_login_no_external_redirect(webtest_loggedout):
    """Ensure that the login page won't redirect to an external site."""
    login_page = webtest_loggedout.get(
        "/login", params={"from_url": "http://example.com"}
    )
    login_page.form["username"] = "SessionUser"
    login_page.form["password"] = "session user password"
    response = login_page.form.submit()

    assert response.status_int == 302
    assert "example.com" not in response.headers["Location"]
