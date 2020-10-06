# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains tasks that can be run through the invoke tool."""

import re
from pathlib import Path

from invoke import task


@task
def update_pip_requirements(context):
    """Use pip-tools to update package versions in the requirements files."""

    def build_and_clean(context, name):
        """Update a pip requirements file and clean up the result."""
        in_filename = Path(name).with_suffix(".in")
        out_filename = Path(name).with_suffix(".txt")

        print(f"Updating package versions from {in_filename}")
        context.run(f"pip-compile --no-header --quiet --upgrade {in_filename}")

        # Salt's pip module is currently broken if any comments in the requirements
        # file have "-r" in them, so we need to remove all of those comments
        with open(out_filename, "r") as req_file:
            req_lines = req_file.readlines()

        # remove any comments that include an -r reference
        # (meaning it's a package that was specifically installed, not a dependency)
        cleaned_lines = [re.sub(r"\s+# via.*-r.*", "", line) for line in req_lines]

        with open(out_filename, "w") as req_file:
            req_file.writelines(cleaned_lines)

    build_and_clean(context, "requirements")
    build_and_clean(context, "requirements-dev")
