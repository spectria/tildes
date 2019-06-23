# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Script for cleaning up private/deleted data.

Other things that should probably be added here eventually:
    - Delete individual votes on comments/topics after voting has been closed
    - Delete which users labeled comments after labeling has been closed
    - Delete old used invite codes (30 days after used?)
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy.orm.session import Session
from sqlalchemy.sql.expression import text

from tildes.lib.database import get_session_from_config
from tildes.models.comment import (
    Comment,
    CommentBookmark,
    CommentLabel,
    CommentNotification,
    CommentVote,
)
from tildes.models.group import GroupSubscription
from tildes.models.log import Log
from tildes.models.topic import Topic, TopicBookmark, TopicVisit, TopicVote
from tildes.models.user import User, UserGroupSettings


# sensitive data older than this should be removed
RETENTION_PERIOD = timedelta(days=30)

# used to set a column back to its default value
DEFAULT = text("DEFAULT")


def clean_all_data(config_path: str) -> None:
    """Clean all private/deleted data.

    This should generally be the only function called in most cases, and will initiate
    the full cleanup process.
    """
    db_session = get_session_from_config(config_path)

    cleaner = DataCleaner(db_session, RETENTION_PERIOD)
    cleaner.clean_all()


class DataCleaner:
    """Container class for all methods related to cleaning up old data."""

    def __init__(self, db_session: Session, retention_period: timedelta):
        """Create a new DataCleaner."""
        self.db_session = db_session
        self.retention_cutoff = datetime.now() - retention_period

        # set high timeout for this script, since cleanup can activate a lot of triggers
        self.db_session.execute("SET statement_timeout TO '10min'")

    def clean_all(self) -> None:
        """Call all the cleanup functions."""
        logging.info(f"Cleaning up all data (retention cutoff {self.retention_cutoff})")

        self.delete_old_log_entries()
        self.delete_old_topic_visits()

        self.clean_old_deleted_comments()
        self.clean_old_deleted_topics()
        self.clean_old_deleted_users()

        self.clean_old_deleted_user_data()

    def delete_old_log_entries(self) -> None:
        """Delete all log entries older than the retention cutoff.

        Note that this will also delete all entries from the child tables that inherit
        from Log (LogTopics, etc.).
        """
        deleted = (
            self.db_session.query(Log)
            .filter(Log.event_time <= self.retention_cutoff)
            .delete(synchronize_session=False)
        )
        self.db_session.commit()
        logging.info(f"Deleted {deleted} old log entries.")

    def delete_old_topic_visits(self) -> None:
        """Delete all topic visits older than the retention cutoff."""
        deleted = (
            self.db_session.query(TopicVisit)
            .filter(TopicVisit.visit_time <= self.retention_cutoff)
            .delete(synchronize_session=False)
        )
        self.db_session.commit()
        logging.info(f"Deleted {deleted} old topic visits.")

    def clean_old_deleted_comments(self) -> None:
        """Clean the data of old deleted comments.

        Change the comment's author to the "unknown user" (id 0), and delete its
        contents.
        """
        updated = (
            self.db_session.query(Comment)
            .filter(
                Comment.is_deleted == True,  # noqa
                Comment.deleted_time <= self.retention_cutoff,  # type: ignore
                Comment.user_id != 0,
            )
            .update(
                {
                    "user_id": 0,
                    "last_edited_time": DEFAULT,
                    "markdown": "",
                    "rendered_html": "",
                    "excerpt": "",
                },
                synchronize_session=False,
            )
        )
        self.db_session.commit()
        logging.info(f"Cleaned {updated} old deleted comments.")

    def clean_old_deleted_topics(self) -> None:
        """Clean the data of old deleted topics.

        Change the topic's author to the "unknown user" (id 0), and delete its title,
        contents, tags, and metadata.
        """
        updated = (
            self.db_session.query(Topic)
            .filter(
                Topic.is_deleted == True,  # noqa
                Topic.deleted_time <= self.retention_cutoff,  # type: ignore
                Topic.user_id != 0,
            )
            .update(
                {
                    "user_id": 0,
                    "last_edited_time": DEFAULT,
                    "title": "",
                    "topic_type": DEFAULT,
                    "markdown": DEFAULT,
                    "rendered_html": DEFAULT,
                    "link": DEFAULT,
                    "original_url": DEFAULT,
                    "content_metadata": DEFAULT,
                    "_tags": DEFAULT,
                },
                synchronize_session=False,
            )
        )
        self.db_session.commit()
        logging.info(f"Cleaned {updated} old deleted topics.")

    def clean_old_deleted_users(self) -> None:
        """Clean the data of old deleted users."""
        updated = (
            self.db_session.query(User)
            .filter(
                User.is_deleted == True,  # noqa
                User.deleted_time <= self.retention_cutoff,  # type: ignore
                User.password_hash != "",
            )
            .update(
                {
                    "password_hash": "",
                    "email_address_hash": DEFAULT,
                    "email_address_note": DEFAULT,
                    "two_factor_enabled": DEFAULT,
                    "two_factor_secret": DEFAULT,
                    "two_factor_backup_codes": DEFAULT,
                    "inviter_id": DEFAULT,
                    "invite_codes_remaining": DEFAULT,
                    "track_comment_visits": DEFAULT,
                    "collapse_old_comments": DEFAULT,
                    "auto_mark_notifications_read": DEFAULT,
                    "open_new_tab_external": DEFAULT,
                    "open_new_tab_internal": DEFAULT,
                    "open_new_tab_text": DEFAULT,
                    "theme_default": DEFAULT,
                    "permissions": DEFAULT,
                    "home_default_order": DEFAULT,
                    "home_default_period": DEFAULT,
                    "_filtered_topic_tags": DEFAULT,
                    "comment_label_weight": DEFAULT,
                    "last_exemplary_label_time": DEFAULT,
                    "_bio_markdown": DEFAULT,
                    "bio_rendered_html": DEFAULT,
                },
                synchronize_session=False,
            )
        )
        self.db_session.commit()
        logging.info(f"Cleaned {updated} old deleted users.")

    def clean_old_deleted_user_data(self) -> None:
        """Clean additional data from deleted users (subscriptions, votes, etc.)."""
        models_to_delete_from = [
            CommentBookmark,
            CommentLabel,
            CommentNotification,
            CommentVote,
            GroupSubscription,
            TopicBookmark,
            TopicVote,
            UserGroupSettings,
        ]

        user_id_subquery = (
            self.db_session.query(User.user_id)
            .filter(
                User.is_deleted == True,  # noqa
                User.deleted_time <= self.retention_cutoff,  # type: ignore
            )
            .subquery()
        )

        for model_cls in models_to_delete_from:
            deleted = (
                self.db_session.query(model_cls)
                .filter(model_cls.user_id.in_(user_id_subquery))  # type: ignore
                .delete(synchronize_session=False)
            )
            self.db_session.commit()
            logging.info(f"Deleted {deleted} rows from {model_cls.__name__}.")
