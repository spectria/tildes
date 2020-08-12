# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Global-like settings for the application.

This module should always be imported as a whole ("from tildes import settings"), not
importing individual names, since that will cause re-initialization.

Currently, this module only contains a dict with some of the settings defined in the
INI file, specifically ones with the "tildes." prefix. The values in this dict are
initialized during app startup.

Important note: this module may be a terrible idea and I may regret this.
"""

from pyramid.config import Configurator

INI_FILE_SETTINGS = {}


def includeme(config: Configurator) -> None:
    """Initialize ini_file_settings with all prefixed settings from the INI file."""
    global INI_FILE_SETTINGS  # pylint: disable=global-statement
    setting_prefix = "tildes."

    INI_FILE_SETTINGS = {
        setting[len(setting_prefix) :]: value
        for setting, value in config.get_settings().items()
        if setting.startswith(setting_prefix)
    }
