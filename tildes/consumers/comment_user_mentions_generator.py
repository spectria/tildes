"""Consumer that generates user mentions for comments."""

from amqpy import Message

from tildes.lib.amqp import PgsqlQueueConsumer
from tildes.models.comment import Comment, CommentNotification


class CommentUserMentionGenerator(PgsqlQueueConsumer):
    """Consumer that generates user mentions for comments."""

    def run(self, msg: Message) -> None:
        """Process a delivered message."""
        comment = (
            self.db_session.query(Comment)
            .filter_by(comment_id=msg.body['comment_id'])
            .one()
        )
        new_mentions = CommentNotification.get_mentions_for_comment(
            self.db_session, comment)

        if msg.delivery_info['routing_key'] == 'comment.created':
            for user_mention in new_mentions:
                self.db_session.add(user_mention)
        elif msg.delivery_info['routing_key'] == 'comment.edited':
            to_delete, to_add = (
                CommentNotification.prevent_duplicate_notifications(
                    self.db_session, comment, new_mentions))

            for user_mention in to_delete:
                self.db_session.delete(user_mention)

            for user_mention in to_add:
                self.db_session.add(user_mention)


if __name__ == '__main__':
    CommentUserMentionGenerator(
        queue_name='comment_user_mentions_generator.q',
        routing_keys=['comment.created', 'comment.edited'],
    ).consume_queue()
