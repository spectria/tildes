# Copyright (c) 2020 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Model wrappers that control which data and methods are accessible for scripting.

Each wrapper class needs to have "gettable_attrs" and/or "settable_attrs" properties
that define which attributes (including methods) are accessible from inside scripts.
"""

from wrapt import ObjectProxy

from tildes.lib.lua import SandboxedLua

from .comment import Comment
from .topic import Topic
from .user import User


class UserScriptingWrapper(ObjectProxy):
    # pylint: disable=abstract-method
    """Wrapper for the User model."""

    gettable_attrs = {"username"}

    def __init__(self, user: User, lua_sandbox: SandboxedLua):
        """Wrap a User."""
        super().__init__(user)

        self._lua = lua_sandbox.lua


class TopicScriptingWrapper(ObjectProxy):
    # pylint: disable=abstract-method
    """Wrapper for the Topic model."""

    gettable_attrs = {
        "is_link_type",
        "is_text_type",
        "link",
        "link_domain",
        "markdown",
        "remove",
        "tags",
        "title",
        "user",
    }
    settable_attrs = {"link", "tags", "title"}

    def __init__(self, topic: Topic, lua_sandbox: SandboxedLua):
        """Wrap a Topic."""
        super().__init__(topic)

        self._lua = lua_sandbox.lua

        self.user = UserScriptingWrapper(topic.user, lua_sandbox)

    @property
    def tags(self):  # type: ignore
        """Return the topic's tags as a Lua table."""
        return self._lua.table_from(self.__wrapped__.tags)

    @tags.setter
    def tags(self, new_tags):  # type: ignore
        """Set the topic's tags, the new value should be a Lua table."""
        self.__wrapped__.tags = new_tags.values()

    def remove(self) -> None:
        """Remove the topic."""
        self.__wrapped__.is_removed = True


class CommentScriptingWrapper(ObjectProxy):
    # pylint: disable=abstract-method
    """Wrapper for the Comment model."""

    gettable_attrs = {"markdown", "remove", "topic", "user"}

    def __init__(self, comment: Comment, lua_sandbox: SandboxedLua):
        """Wrap a Comment."""
        super().__init__(comment)

        self._lua = lua_sandbox.lua

        self.topic = TopicScriptingWrapper(comment.topic, lua_sandbox)
        self.user = UserScriptingWrapper(comment.user, lua_sandbox)

    def remove(self) -> None:
        """Remove the comment."""
        self.__wrapped__.is_removed = True
