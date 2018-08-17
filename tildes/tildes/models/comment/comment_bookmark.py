"""Contains the CommentBookmark class."""

from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from tildes.models import DatabaseModel
from tildes.models.comment import Comment
from tildes.models.user import User


class CommentBookmark(DatabaseModel):
    """Model for a comment bookmark."""

    __tablename__ = "comment_bookmarks"

    user_id: int = Column(
        Integer, ForeignKey("users.user_id"), nullable=False, primary_key=True
    )
    comment_id: int = Column(
        Integer, ForeignKey("comments.comment_id"), nullable=False, primary_key=True
    )
    created_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        server_default=text("NOW()"),
    )

    user: User = relationship("User", innerjoin=True)
    comment: Comment = relationship("Comment", innerjoin=True)

    def __init__(self, user: User, comment: Comment) -> None:
        """Create a new comment bookmark."""
        self.user = user
        self.comment = comment
