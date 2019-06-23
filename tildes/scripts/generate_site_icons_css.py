# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Script to generate CSS related to site icons based on which have been downloaded."""

import os
import shutil
import stat
from tempfile import NamedTemporaryFile


ICON_FOLDER = "/opt/tildes/static/images/site-icons"
OUTPUT_FILE = "/opt/tildes/static/css/site-icons.css"

CSS_RULE = """
.topic-icon-{domain} {{
  background-image: url('/images/site-icons/{filename}');
  border: 0;
}}
"""


def _is_output_file_outdated() -> bool:
    """Return whether the output file needs an update yet."""
    # check if any icon files have a modified time higher than the output file's
    try:
        output_file_modified = os.stat(OUTPUT_FILE).st_mtime
    except FileNotFoundError:
        return True

    for entry in os.scandir(ICON_FOLDER):
        if entry.stat().st_mtime > output_file_modified:
            return True

    return False


def generate_css() -> None:
    """Generate the CSS file for site icons and replace the old one."""
    if not _is_output_file_outdated():
        return

    with NamedTemporaryFile(mode="w") as temp_file:
        for filename in os.listdir(ICON_FOLDER):
            split_filename = filename.split(".")
            if len(split_filename) < 2 or split_filename[1] != "png":
                continue

            temp_file.write(
                CSS_RULE.format(domain=split_filename[0], filename=filename)
            )

        temp_file.flush()
        shutil.copy(temp_file.name, OUTPUT_FILE)

    # set file permissions to 644 (rw-r--r--)
    os.chmod(OUTPUT_FILE, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
