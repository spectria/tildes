# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Consumer that runs processing scripts on posts."""

from sqlalchemy import desc
from sqlalchemy.sql.expression import or_

from tildes.lib.event_stream import EventStreamConsumer, Message
from tildes.lib.lua import SandboxedLua
from tildes.models.comment import Comment
from tildes.models.group import GroupScript
from tildes.models.scripting import CommentScriptingWrapper, TopicScriptingWrapper
from tildes.models.topic import Topic


class PostProcessingScriptRunner(EventStreamConsumer):
    """Consumer that generates content_metadata for topics."""

    METRICS_PORT = 25016

    def process_message(self, message: Message) -> None:
        """Process a message from the stream."""
        if "topic_id" in message.fields:
            post = (
                self.db_session.query(Topic)
                .filter_by(topic_id=message.fields["topic_id"])
                .one()
            )
            wrapper_class = TopicScriptingWrapper
            group = post.group
        elif "comment_id" in message.fields:
            post = (
                self.db_session.query(Comment)
                .filter_by(comment_id=message.fields["comment_id"])
                .one()
            )
            wrapper_class = CommentScriptingWrapper
            group = post.topic.group

        if post.is_deleted:
            return

        scripts_to_run = (
            self.db_session.query(GroupScript)
            .filter(or_(GroupScript.group == None, GroupScript.group == group))  # noqa
            .order_by(desc(GroupScript.group_id))  # sort the global script first
            .all()
        )

        for script in scripts_to_run:
            lua_sandbox = SandboxedLua()
            lua_sandbox.run_code(script.code)

            wrapped_post = wrapper_class(post, lua_sandbox)

            try:
                if isinstance(post, Topic):
                    lua_sandbox.run_lua_function("on_topic_post", wrapped_post)
                elif isinstance(post, Comment):
                    lua_sandbox.run_lua_function("on_comment_post", wrapped_post)
            except ValueError:
                pass


if __name__ == "__main__":
    PostProcessingScriptRunner(
        "post_processing_script_runner",
        source_streams=[
            "comments.insert",
            "topics.insert",
        ],
    ).consume_streams()
