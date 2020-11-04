# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains tasks that can be run through the invoke tool."""

from pathlib import Path

from invoke import task
from invoke.exceptions import Exit


def output(string):
    """Output a string without a line ending and flush immediately."""
    print(string, end="", flush=True)


@task
def web_server_reload(context):
    """Reload the web server, in order to apply config updates."""
    context.run("sudo systemctl reload nginx.service")


@task(help={"full": "Include all checks (very slow)"})
def code_style_check(context, full=False):
    """Run the various utilities to check code style.

    By default, runs checks that return relatively quickly. To run the full set of
    checks (which will be quite slow), add the --full flag.
    """
    output("Checking if Black would reformat any Python code... ")
    context.run("black --check .")

    print("Checking SCSS style...", flush=True)
    context.run("npm run --silent lint:scss")

    print("Checking JS style...", flush=True)
    context.run("npm run --silent lint:js")

    if full:
        output("Checking Python style fully (takes a couple minutes)... ")

        # -M flag hides the "summary information"
        context.run("prospector -M")


@task
def pip_requirements_update(context):
    """Use pip-tools to update package versions in the requirements files."""

    for filename in ("requirements.in", "requirements-dev.in"):
        print(f"Updating package versions from {filename}")
        context.run(
            f"pip-compile --no-header --no-annotate --quiet --upgrade {filename}"
        )


@task
def shell(context):
    """Start an IPython shell inside the app environment.

    Will use the settings in production.ini if that file exists, otherwise will fall
    back to using development.ini.
    """
    if Path("production.ini").exists():
        context.run("pshell production.ini", pty=True)
    else:
        context.run("pshell development.ini", pty=True)


@task(
    help={
        "full": "Include all tests",
        "html-validation": "Include HTML validation (very slow, includes webtests)",
        "quiet": "Reduce verbosity",
        "webtests": "Include webtests (a little slow)",
    }
)
def test(context, full=False, quiet=False, webtests=False, html_validation=False):
    """Run the tests.

    By default, webtests (ones that make actual HTTP requests to the app) and HTML
    validation tests (checking the validity of the HTML on some of the site's pages) are
    not run because they are slow, but you can include them with the appropriate flag.
    """
    # webtests are required as part of HTML validation
    if html_validation:
        webtests = True

    pytest_args = []
    excluded_markers = []

    if not full:
        if not webtests:
            excluded_markers.append("webtest")
        if not html_validation:
            excluded_markers.append("html_validation")

    if excluded_markers:
        excluded_marker_str = " or ".join(excluded_markers)
        pytest_args.append(f'-m "not ({excluded_marker_str})"')

    if quiet:
        output("Running tests... ")

        pytest_args.append("-q")
        result = context.run("pytest " + " ".join(pytest_args), hide=True)

        # only output the final line of pytest's stdout (test count + runtime)
        print(result.stdout.splitlines()[-1])
    else:
        context.run("pytest " + " ".join(pytest_args), pty=True)


@task(
    help={
        "domain": "Domain to obtain a cert for (can be specified multiple times)",
    },
    iterable=["domain"],
    post=[web_server_reload],
)
def tls_certificate_renew(context, domain, wildcard=True):
    """Renew the TLS certificate for the specified domain(s)."""
    if not domain:
        raise Exit("No domains specified")

    domains = []
    for dom in domain:
        domains.append(dom)
        if wildcard:
            domains.append(f"*.{dom}")

    domain_args = " ".join([f"-d {dom}" for dom in domains])

    context.run(
        f"sudo certbot certonly --manual {domain_args} "
        "--preferred-challenges dns-01 "
        "--server https://acme-v02.api.letsencrypt.org/directory"
    )


@task
def type_check(context):
    """Run static type checking on the Python code."""
    output("Running static type checking... ")
    context.run("mypy .")
