# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Consumer that generates user mentions for comments."""

from tildes.lib.event_stream import EventStreamConsumer, Message
from tildes.models.comment import Comment, CommentNotification


class CommentUserMentionGenerator(EventStreamConsumer):
    """Consumer that generates user mentions for comments."""

    def process_message(self, message: Message) -> None:
        """Process a message from the stream."""
        comment = (
            self.db_session.query(Comment)
            .filter_by(comment_id=message.fields["comment_id"])
            .one()
        )

        # don't generate mentions for deleted/removed comments
        if comment.is_deleted or comment.is_removed:
            return

        new_mentions = CommentNotification.get_mentions_for_comment(
            self.db_session, comment
        )

        if message.stream == "comments.insert":
            for user_mention in new_mentions:
                self.db_session.add(user_mention)
        elif message.stream == "comments.update.markdown":
            to_delete, to_add = CommentNotification.prevent_duplicate_notifications(
                self.db_session, comment, new_mentions
            )

            for user_mention in to_delete:
                self.db_session.delete(user_mention)

            for user_mention in to_add:
                self.db_session.add(user_mention)


if __name__ == "__main__":
    CommentUserMentionGenerator(
        "comment_user_mentions_generator",
        source_streams=["comments.insert", "comments.update.markdown"],
    ).consume_streams()
