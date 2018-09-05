# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from webassets.loaders import YAMLLoader


WEBASSETS_ENV = YAMLLoader("webassets.yaml").load_environment()


def test_scripts_file_first_in_bundle():
    """Ensure that the main scripts.js file will be at the top."""
    js_bundle = WEBASSETS_ENV["javascript"]

    first_filename = js_bundle.resolve_contents()[0][0]

    assert first_filename == "js/scripts.js"


def test_styles_file_last_in_bundle():
    """Ensure that the main styles.css file will be at the bottom."""
    css_bundle = WEBASSETS_ENV["css"]

    last_filename = css_bundle.resolve_contents()[-1][0]

    assert last_filename == "css/styles.css"
