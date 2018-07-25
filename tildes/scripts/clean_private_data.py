"""Script for cleaning up private/deleted data.

Other things that should probably be added here eventually:
    - Delete individual votes on comments/topics after voting has been closed
    - Delete which users tagged comments after tagging has been closed
    - Delete old used invite codes (30 days after used?)
"""

from datetime import datetime, timedelta
import logging

from sqlalchemy.orm.session import Session

from tildes.lib.database import get_session_from_config
from tildes.models.comment import Comment
from tildes.models.log import Log
from tildes.models.topic import Topic, TopicVisit


# sensitive data older than this should be removed
RETENTION_PERIOD = timedelta(days=30)


def clean_all_data(config_path: str) -> None:
    """Clean all private/deleted data.

    This should generally be the only function called in most cases, and will
    initiate the full cleanup process.
    """
    db_session = get_session_from_config(config_path)

    cleaner = DataCleaner(db_session, RETENTION_PERIOD)
    cleaner.clean_all()


class DataCleaner():
    """Container class for all methods related to cleaning up old data."""

    def __init__(
            self,
            db_session: Session,
            retention_period: timedelta,
    ) -> None:
        """Create a new DataCleaner."""
        self.db_session = db_session
        self.retention_cutoff = datetime.now() - retention_period

    def clean_all(self) -> None:
        """Call all the cleanup functions."""
        logging.info(
            f'Cleaning up all data (retention cutoff {self.retention_cutoff})')

        self.delete_old_log_entries()
        self.delete_old_topic_visits()

        self.clean_old_deleted_comments()
        self.clean_old_deleted_topics()

    def delete_old_log_entries(self) -> None:
        """Delete all log entries older than the retention cutoff.

        Note that this will also delete all entries from the child tables that
        inherit from Log (LogTopics, etc.).
        """
        deleted = (
            self.db_session.query(Log)
            .filter(Log.event_time <= self.retention_cutoff)
            .delete(synchronize_session=False)
        )
        self.db_session.commit()
        logging.info(f'Deleted {deleted} old log entries.')

    def delete_old_topic_visits(self) -> None:
        """Delete all topic visits older than the retention cutoff."""
        deleted = (
            self.db_session.query(TopicVisit)
            .filter(TopicVisit.visit_time <= self.retention_cutoff)
            .delete(synchronize_session=False)
        )
        self.db_session.commit()
        logging.info(f'Deleted {deleted} old topic visits.')

    def clean_old_deleted_comments(self) -> None:
        """Clean the data of old deleted comments.

        Change the comment's author to the "unknown user" (id 0), and delete
        its contents.
        """
        updated = (
            self.db_session.query(Comment)
            .filter(
                Comment.deleted_time <= self.retention_cutoff,  # type: ignore
                Comment.user_id != 0,
            )
            .update({
                'user_id': 0,
                'markdown': '',
                'rendered_html': '',
            }, synchronize_session=False)
        )
        self.db_session.commit()
        logging.info(f'Cleaned {updated} old deleted comments.')

    def clean_old_deleted_topics(self) -> None:
        """Clean the data of old deleted topics.

        Change the topic's author to the "unknown user" (id 0), and delete its
        title, contents, tags, and metadata.
        """
        updated = (
            self.db_session.query(Topic)
            .filter(
                Topic.deleted_time <= self.retention_cutoff,  # type: ignore
                Topic.user_id != 0,
            )
            .update({
                'user_id': 0,
                'title': '',
                'topic_type': 'TEXT',
                'markdown': None,
                'rendered_html': None,
                'link': None,
                'content_metadata': None,
                '_tags': [],
            }, synchronize_session=False)
        )
        self.db_session.commit()
        logging.info(f'Cleaned {updated} old deleted topics.')
