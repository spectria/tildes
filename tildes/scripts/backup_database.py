# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Script to dump the database, compress and encrypt it, and upload to an FTP.

The script will also delete any old backups present locally and remotely if they are
older than the (individual) retention periods specified.

Warning: this script is *not* robust. It assumes that a number of preconditions are in
place, and will probably just crash completely if they aren't:
    * lftp and gpg are installed
    * A netrc file exists for the user with credentials for the FTP
    * The specified GPG recipient's public key is in the keyring
"""

import logging
import os
import subprocess
from datetime import datetime, timedelta
from ftplib import FTP
from netrc import netrc

import click


FILENAME_FORMAT = "backup-%Y-%m-%dT%H:%M"

REMOTE_RETENTION_PERIOD = timedelta(days=30)
LOCAL_RETENTION_PERIOD = timedelta(days=7)


def create_encrypted_backup(gpg_recipient: str) -> str:
    """Dump the database, compress, and encrypt with GPG, returning final filename."""
    filename = datetime.now().strftime(FILENAME_FORMAT)

    # dump the database to a file
    with open(f"{filename}.sql", "w") as dump_file:
        subprocess.run(
            ["pg_dump", "-U", "tildes", "tildes"], stdout=dump_file, text=True
        )

    # gzip the dump file (replaces it)
    subprocess.run(["gzip", "-9", f"{filename}.sql"])

    # encrypt the compressed dump file using gpg
    subprocess.run(
        [
            "gpg",
            "--output",
            f"{filename}.sql.gz.gpg",
            "--encrypt",
            "--recipient",
            gpg_recipient,
            f"{filename}.sql.gz",
        ]
    )

    # delete the unencrypted dump file
    os.remove(f"{filename}.sql.gz")

    return f"{filename}.sql.gz.gpg"


def upload_new_backup(host: str, gpg_recipient: str) -> None:
    """Create a new (encrypted) backup and then upload it to the FTP."""
    new_filename = create_encrypted_backup(gpg_recipient)

    subprocess.run(["lftp", "-e", f"put {new_filename}; bye", host])
    logging.info(f"Successfully uploaded {new_filename} to FTP.")


def get_date_from_backup_filename(filename: str) -> datetime:
    """Determine the date from a backup filename.

    Raises ValueError for all filenames that don't match the backup filename format.
    """
    try:
        return datetime.strptime(filename, f"{FILENAME_FORMAT}.sql.gz.gpg")
    except ValueError:
        # also try the old obsolete filename format, with no time info
        # will raise ValueError itself if this fails too
        return datetime.strptime(filename, "backup-%Y-%m-%d.sql.gz.gpg")


def delete_old_backups(host: str) -> None:
    """Delete all backups older than the retention period, both locally and remotely."""
    delete_old_local_backups()
    delete_old_remote_backups(host)


def delete_old_local_backups() -> None:
    """Delete all local backups older than the local retention period."""
    for filename in os.listdir():
        try:
            backup_date = get_date_from_backup_filename(filename)
        except ValueError:
            # not one of the backup files, ignore it
            continue

        if datetime.now() - backup_date > LOCAL_RETENTION_PERIOD:
            os.remove(filename)
            logging.info(f"Deleted local backup {filename}")


def delete_old_remote_backups(host: str) -> None:
    """Connect to FTP and delete all backups older than the remote retention period."""
    credentials = netrc()

    ftp_credentials = credentials.authenticators(host)
    if not ftp_credentials:
        raise RuntimeError("netrc file does not contain credentials for this host")

    username, _, password = ftp_credentials
    if not username or not password:
        raise RuntimeError("netrc file is missing username or password")

    with FTP(host, username, password) as ftp:
        for filename, _ in ftp.mlsd():
            try:
                backup_date = get_date_from_backup_filename(filename)
            except ValueError:
                # not one of the backup files, just ignore it
                continue

            if datetime.now() - backup_date > REMOTE_RETENTION_PERIOD:
                ftp.delete(filename)
                logging.info(f"Deleted remote backup {filename}")


@click.command()
@click.option("--host", required=True, help="The remote FTP host to use")
@click.option(
    "--gpg-recipient",
    required=True,
    help="The recipient (email address) to use for GPG encryption",
)
def backup_and_clean_up(host: str = "", gpg_recipient: str = "") -> None:
    """Create and upload a new backup, then clean up old ones (main command)."""
    upload_new_backup(host, gpg_recipient)
    delete_old_backups(host)


if __name__ == "__main__":
    backup_and_clean_up()
