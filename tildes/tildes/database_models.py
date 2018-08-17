"""Module that imports all DatabaseModel subclasses.

This module shouldn't really be used for anything directly. It's for convenience so that
both Alembic and the script for initializing the database can simply import * from here.
"""
# pylint: disable=unused-import

from tildes.models.comment import (
    Comment,
    CommentBookmark,
    CommentLabel,
    CommentNotification,
    CommentVote,
)
from tildes.models.group import Group, GroupSubscription
from tildes.models.log import Log
from tildes.models.message import MessageConversation, MessageReply
from tildes.models.scraper import ScraperResult
from tildes.models.topic import Topic, TopicBookmark, TopicVisit, TopicVote
from tildes.models.user import User, UserGroupSettings, UserInviteCode
