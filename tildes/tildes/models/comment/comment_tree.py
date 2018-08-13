"""Contains the CommentTree class."""

from typing import Iterator, List, Optional, Sequence

from prometheus_client import Histogram

from tildes.enums import CommentSortOption
from tildes.metrics import get_histogram
from .comment import Comment


class CommentTree:
    """Class representing the tree of comments on a particular topic.

    The Comment objects held by this class have additional attributes added:
        - `replies`: the list of all immediate children to that comment
        - `has_visible_descendant`: whether the comment has any visible
            descendants (if not, it can be pruned from the tree)
    """

    def __init__(self, comments: Sequence[Comment], sort: CommentSortOption) -> None:
        """Create a sorted CommentTree from a flat list of Comments."""
        self.tree: List[Comment] = []
        self.sort = sort

        # sort the comments by date, since replies will always be posted later
        # this will ensure that parent comments are always processed first
        self.comments = sorted(comments, key=lambda c: c.created_time)

        # if there aren't any comments, we can just bail out here
        if not self.comments:
            return

        self._build_tree()

        # The method of building the tree already sorts it by posting time, so
        # there's no need to sort again if that's the desired sorting. Note
        # also that because _sort_tree() uses sorted() which is a stable sort,
        # this means that the "secondary sort" will always be by posting time
        # as well.
        if sort != CommentSortOption.POSTED:
            with self._sorting_histogram().time():
                self.tree = self._sort_tree(self.tree, self.sort)

        self.tree = self._prune_empty_branches(self.tree)

    def _build_tree(self) -> None:
        """Build the initial tree from the flat list of Comments."""
        comments_by_id = {}

        for comment in self.comments:
            comment.replies = []
            comment.has_visible_descendant = False
            comments_by_id[comment.comment_id] = comment

            if comment.parent_comment_id:
                parent_comment = comments_by_id[comment.parent_comment_id]
                parent_comment.replies.append(comment)

                # if this comment isn't deleted, work back up towards the root,
                # indicating to all parents they have a visible descendant
                if not comment.is_deleted:
                    while not parent_comment.has_visible_descendant:
                        parent_comment.has_visible_descendant = True

                        if not parent_comment.parent_comment_id:
                            break

                        next_parent_id = parent_comment.parent_comment_id
                        parent_comment = comments_by_id[next_parent_id]
            else:
                self.tree.append(comment)

    @staticmethod
    def _sort_tree(tree: List[Comment], sort: CommentSortOption) -> List[Comment]:
        """Sort the tree by the desired ordering (recursively).

        Because Python's sorted() function is stable, the ordering of any
        comments that compare equal on the sorting method will be the same as
        the order that they were originally in when passed to this function.
        """
        if sort == CommentSortOption.NEWEST:
            tree = sorted(tree, key=lambda c: c.created_time, reverse=True)
        elif sort == CommentSortOption.POSTED:
            tree = sorted(tree, key=lambda c: c.created_time)
        elif sort == CommentSortOption.VOTES:
            tree = sorted(tree, key=lambda c: c.num_votes, reverse=True)

        for comment in tree:
            if not comment.has_visible_descendant:
                # no need to bother sorting replies if none will be visible
                continue

            comment.replies = CommentTree._sort_tree(comment.replies, sort)

        return tree

    @staticmethod
    def _prune_empty_branches(tree: Sequence[Comment]) -> List[Comment]:
        """Remove branches from the tree with no visible comments."""
        pruned_tree = []

        for comment in tree:
            if comment.is_deleted and not comment.has_visible_descendant:
                # prune this branch from the tree
                continue

            # recursively prune the tree of replies to this comment
            replies = CommentTree._prune_empty_branches(comment.replies)
            comment.replies = replies

            pruned_tree.append(comment)

        return pruned_tree

    def __iter__(self) -> Iterator[Comment]:
        """Iterate over the (top-level) Comments in the tree."""
        for comment in self.tree:
            yield comment

    def __len__(self) -> int:
        """Return the number of comments in the tree (including deleted)."""
        return len(self.comments)

    @property
    def num_top_level(self) -> int:
        """Return the number of top-level comments in the tree."""
        return len(self.tree)

    @property
    def most_recent_comment(self) -> Optional[Comment]:
        """Return the most recent non-deleted Comment in the tree."""
        for comment in reversed(self.comments):
            if not comment.is_deleted:
                return comment

        return None

    def _sorting_histogram(self) -> Histogram:
        """Return the (labeled) histogram to use for timing the sorting."""
        num_comments = len(self.comments)

        # make an "order of magnitude" label based on the number of comments
        if num_comments == 0:
            raise ValueError("Attempting to time an empty comment tree sort")
        if num_comments < 10:
            num_comments_range = "1 - 9"
        elif num_comments < 100:
            num_comments_range = "10 - 99"
        elif num_comments < 1000:
            num_comments_range = "100 - 999"
        else:
            num_comments_range = "1000+"

        return get_histogram(
            "comment_tree_sorting",
            num_comments_range=num_comments_range,
            order=self.sort.name,
        )
