# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Command-line tools for managing a breached-passwords bloom filter.

This tool will help with creating and updating a bloom filter in Redis (using ReBloom:
https://github.com/RedisLabsModules/rebloom) to hold hashes for passwords that have been
revealed through data breaches (to prevent users from using these passwords here). The
dumps are likely primarily sourced from Troy Hunt's "Pwned Passwords" files:
https://haveibeenpwned.com/Passwords

Specifically, the commands in this tool allow building the bloom filter somewhere else,
then the RDB file can be transferred to the production server.  Note that it is expected
that a separate redis server instance is running solely for holding this bloom filter.
Replacing the RDB file will result in all other keys being lost.

Expected usage of this tool should look something like:

On the machine building the bloom filter:
    python breached_passwords.py init --estimate 350000000
    python breached_passwords.py addhashes pwned-passwords-1.0.txt
    python breached_passwords.py addhashes pwned-passwords-update-1.txt

Then the RDB file can simply be transferred to the production server, overwriting any
previous RDB file.

"""

import subprocess
from typing import Any

import click
from redis import Redis, ResponseError

from tildes.lib.password import (
    BREACHED_PASSWORDS_BF_KEY,
    BREACHED_PASSWORDS_REDIS_SOCKET,
)


REDIS = Redis(unix_socket_path=BREACHED_PASSWORDS_REDIS_SOCKET)


def generate_redis_protocol(*elements: Any) -> str:
    """Generate a command in the Redis protocol from the specified elements.

    Based on the example Ruby code from
    https://redis.io/topics/mass-insert#generating-redis-protocol
    """
    command = f"*{len(elements)}\r\n"

    for element in elements:
        element = str(element)
        command += f"${len(element)}\r\n{element}\r\n"

    return command


@click.group()
def cli() -> None:
    """Create a functionality-less command group to attach subcommands to."""
    pass


def validate_init_error_rate(ctx: Any, param: Any, value: Any) -> float:
    """Validate the --error-rate arg for the init command."""
    # pylint: disable=unused-argument
    if not 0 < value < 1:
        raise click.BadParameter("error rate must be a float between 0 and 1")

    return value


@cli.command(help="Initialize a new empty bloom filter")
@click.option(
    "--estimate",
    required=True,
    type=int,
    help="Expected number of passwords that will be added",
)
@click.option(
    "--error-rate",
    default=0.01,
    show_default=True,
    help="Bloom filter desired false positive ratio",
    callback=validate_init_error_rate,
)
@click.confirmation_option(
    prompt="Are you sure you want to clear any existing bloom filter?"
)
def init(estimate: int, error_rate: float) -> None:
    """Initialize a new bloom filter (destroying any existing one).

    It generally shouldn't be necessary to re-init a new bloom filter very often with
    this command, only if the previous one was created with too low of an estimate for
    number of passwords, or to change to a different false positive rate. For choosing
    an estimate value, according to the ReBloom documentation: "Performance will begin
    to degrade after adding more items than this number. The actual degradation will
    depend on how far the limit has been exceeded. Performance will degrade linearly as
    the number of entries grow exponentially."
    """
    REDIS.delete(BREACHED_PASSWORDS_BF_KEY)

    # BF.RESERVE {key} {error_rate} {size}
    REDIS.execute_command("BF.RESERVE", BREACHED_PASSWORDS_BF_KEY, error_rate, estimate)

    click.echo(
        "Initialized bloom filter with expected size of {:,} and false "
        "positive rate of {}%".format(estimate, error_rate * 100)
    )


@cli.command(help="Add hashes from a file to the bloom filter")
@click.argument("filename", type=click.Path(exists=True, dir_okay=False))
def addhashes(filename: str) -> None:
    """Add all hashes from a file to the bloom filter.

    This uses the method of generating commands in Redis protocol and feeding them into
    an instance of `redis-cli --pipe`, as recommended in
    https://redis.io/topics/mass-insert
    """
    # make sure the key exists and is a bloom filter
    try:
        REDIS.execute_command("BF.DEBUG", BREACHED_PASSWORDS_BF_KEY)
    except ResponseError:
        click.echo("Bloom filter is not set up properly - run init first.")
        raise click.Abort

    # call wc to count the number of lines in the file for the progress bar
    click.echo("Determining hash count...")
    result = subprocess.run(["wc", "-l", filename], stdout=subprocess.PIPE)
    line_count = int(result.stdout.split(b" ")[0])

    progress_bar: Any = click.progressbar(length=line_count)
    update_interval = 100_000

    click.echo("Adding {:,} hashes to bloom filter...".format(line_count))

    redis_pipe = subprocess.Popen(
        ["redis-cli", "-s", BREACHED_PASSWORDS_REDIS_SOCKET, "--pipe"],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        encoding="utf-8",
    )

    for count, line in enumerate(open(filename), start=1):
        hashval = line.strip().lower()

        # the Pwned Passwords hash lists now have a frequency count for each hash, which
        # is separated from the hash with a colon, so we need to handle that if it's
        # present
        hashval = hashval.split(":")[0]

        command = generate_redis_protocol("BF.ADD", BREACHED_PASSWORDS_BF_KEY, hashval)
        redis_pipe.stdin.write(command)

        if count % update_interval == 0:
            progress_bar.update(update_interval)

    # call SAVE to update the RDB file
    REDIS.save()

    # manually finish the progress bar so it shows 100% and renders properly
    progress_bar.finish()
    progress_bar.render_progress()
    progress_bar.render_finish()


if __name__ == "__main__":
    cli()
