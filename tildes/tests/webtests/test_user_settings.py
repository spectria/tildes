# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later


def test_render_theme_options(webtest):
    """Test that theme settings are being rendered."""
    settings = webtest.get("/settings")
    assert settings.status_int == 200
    assert settings.text.count("(site and account default)") == 1
    assert "(site default)" not in settings.text
    assert "(account default)" not in settings.text
