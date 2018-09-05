# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later


def test_loggedout_username_leak(webtest_loggedout, session_user):
    """Ensure responses from existing and nonexistent users are the same.

    Since logged-out users are currently blocked from seeing user pages, this makes sure
    that there isn't a data leak where it's possible to tell if a particular username
    exists or not.
    """
    existing_user = webtest_loggedout.get(
        "/user/" + session_user.username, expect_errors=True
    )
    nonexistent_user = webtest_loggedout.get(
        "/user/thisdoesntexist", expect_errors=True
    )

    assert existing_user.status == nonexistent_user.status
