# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the CommentTree and CommentInTree classes."""

from datetime import datetime
from typing import Iterator, List, Optional, Sequence, Tuple

from prometheus_client import Histogram
from wrapt import ObjectProxy

from tildes.enums import CommentTreeSortOption
from tildes.metrics import get_histogram
from tildes.models.user import User

from .comment import Comment


class CommentTree:
    """Class representing the tree of comments on a particular topic."""

    def __init__(
        self,
        comments: Sequence[Comment],
        sort: CommentTreeSortOption,
        viewer: Optional[User] = None,
    ):
        """Create a sorted CommentTree from a flat list of Comments."""
        self.tree: List[CommentInTree] = []
        self.sort = sort
        self.viewer = viewer

        # sort the comments by date, since replies will always be posted later this will
        # ensure that parent comments are always processed first
        self.comments = sorted(
            [CommentInTree(comment) for comment in comments],
            key=lambda c: c.created_time,
        )

        self.comments_by_id = {comment.comment_id: comment for comment in comments}

        self._build_tree()

        # The method of building the tree already sorts it by posting time, so there's
        # no need to sort again if that's the desired sorting. Note also that because
        # _sort_tree() uses sorted() which is a stable sort, this means that the
        # "secondary sort" will always be by posting time as well.
        if self.tree and sort != CommentTreeSortOption.POSTED:
            with self._sorting_histogram().time():
                self.tree = self._sort_tree(self.tree, self.sort)

        self.tree = self._prune_empty_branches(self.tree)

        self._count_children()

    def _count_children(self) -> None:
        """Set the num_children attr for all comments."""
        # work backwards through comments so that all children will have their count
        # done first, and we can just sum all the counts from the replies
        for comment in reversed(self.comments):
            for reply in comment.replies:
                comment.num_children += reply.num_children

                if not (reply.is_deleted or reply.is_removed):
                    comment.num_children += 1

    def _build_tree(self) -> None:
        """Build the initial tree from the flat list of Comments."""
        for comment in self.comments:
            if comment.parent_comment_id:
                parent_comment = self.comments_by_id[comment.parent_comment_id]
                parent_comment.replies.append(comment)

                # if this comment isn't deleted, work back up towards the root,
                # indicating to all parents they have a visible descendant
                if not comment.is_deleted:
                    while not parent_comment.has_visible_descendant:
                        parent_comment.has_visible_descendant = True

                        if not parent_comment.parent_comment_id:
                            break

                        next_parent_id = parent_comment.parent_comment_id
                        parent_comment = self.comments_by_id[next_parent_id]
            else:
                self.tree.append(comment)

    @staticmethod
    def _sort_tree(tree: List[Comment], sort: CommentTreeSortOption) -> List[Comment]:
        """Sort the tree by the desired ordering (recursively).

        Because Python's sorted() function is stable, the ordering of any comments that
        compare equal on the sorting method will be the same as the order that they were
        originally in when passed to this function.
        """
        if sort == CommentTreeSortOption.NEWEST:
            tree = sorted(tree, key=lambda c: c.created_time, reverse=True)
        elif sort == CommentTreeSortOption.POSTED:
            tree = sorted(tree, key=lambda c: c.created_time)
        elif sort == CommentTreeSortOption.VOTES:
            tree = sorted(tree, key=lambda c: c.num_votes, reverse=True)
        elif sort == CommentTreeSortOption.RELEVANCE:
            tree = sorted(tree, key=lambda c: c.relevance_sorting_value, reverse=True)

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
            comment.replies = CommentTree._prune_empty_branches(comment.replies)

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

    def collapse_from_labels(self) -> None:
        """Collapse comments based on how they've been labeled."""
        for comment in self.comments:
            # never affect the viewer's own comments
            if comment.user == self.viewer:
                continue

            if comment.is_label_active("noise"):
                comment.collapsed_state = "full"

    def uncollapse_new_comments(self, threshold: datetime) -> None:
        """Mark comments newer than the threshold (and parents) to stay uncollapsed."""
        for comment in reversed(self.comments):
            # as soon as we reach an old comment, we can stop
            if comment.created_time <= threshold:
                break

            if comment.is_deleted or comment.is_removed:
                continue

            # don't apply to the viewer's own comments
            if comment.user == self.viewer:
                continue

            # uncollapse the comment (as long as it hasn't already had its state set)
            if not comment.collapsed_state:
                comment.collapsed_state = "uncollapsed"

            # fetch its direct parent and uncollapse it as well
            if comment.parent_comment_id:
                parent_comment = self.comments_by_id[comment.parent_comment_id]
                parent_comment.collapsed_state = "uncollapsed"

    def finalize_collapsing_maximized(self) -> None:
        """Finish collapsing comments, collapsing as much as possible."""
        # whether the collapsed state of each top-level comment starts out unknown
        top_unknown_initial = [comment.collapsed_state is None for comment in self.tree]

        for comment in self.tree:
            comment.recursively_collapse()

        # if all the top-level comments end up fully collapsed,
        # uncollapse the ones we just collapsed (so we don't have a
        # comment page that's all collapsed comments)
        if all([comment.collapsed_state == "full" for comment in self.tree]):
            for comment, was_unknown in zip(self.tree, top_unknown_initial):
                if was_unknown:
                    comment.collapsed_state = None


class CommentInTree(ObjectProxy):
    # pylint: disable=abstract-method
    """Wrapper for Comments inside a CommentTree that adds some methods/properties."""

    def __init__(self, comment: Comment):
        """Wrap a comment and add the new attributes needed by CommentTree."""
        super().__init__(comment)

        self.collapsed_state: Optional[str] = None
        self.replies: List[CommentInTree] = []
        self.has_visible_descendant = False
        self.num_children = 0

    @property
    def has_uncollapsed_descendant(self) -> bool:
        """Recursively check if the comment has an uncollapsed descendant."""
        for reply in self.replies:
            if reply.collapsed_state == "uncollapsed":
                return True

            if reply.has_uncollapsed_descendant:
                return True

        return False

    def recursively_collapse(self) -> None:
        """Recursively collapse a comment and its replies as much as possible."""
        # stop processing this branch if we hit a fully-collapsed comment
        if self.collapsed_state == "full":
            return

        # if it doesn't have any uncollapsed descendants, collapse the whole branch
        # and stop looking any deeper into it
        if not self.has_uncollapsed_descendant and not self.collapsed_state:
            self.collapsed_state = "full"
            return

        # otherwise (does have uncollapsed descendant), collapse this comment
        # individually if it doesn't already have another state set, then recurse into
        # all branches underneath it
        if not self.collapsed_state:
            self.collapsed_state = "individual"

        for reply in self.replies:
            reply.recursively_collapse()

    @property
    def relevance_sorting_value(self) -> Tuple[int, ...]:
        """Value to use for the comment with the "relevance" comment sorting method.

        Returns a tuple, which allows sorting the comments into "tiers" and then still
        supporting further sorting inside those tiers when it's useful. For example,
        comments labeled as offtopic can be sorted below all non-offtopic comments, but
        then still sorted by votes relative to other offtopic comments.
        """
        if self.is_removed:
            return (-100,)

        if self.is_label_active("noise"):
            return (-2, self.num_votes)

        if self.is_label_active("offtopic"):
            return (-1, self.num_votes)

        if self.is_label_active("joke"):
            return (self.num_votes // 2,)

        # Exemplary comments add 1.0 to the the total weight of the exemplary labels,
        # and multiply the vote count by that. For example, weight 1.0 = votes doubled.
        if self.is_label_active("exemplary"):
            multiplier = self.label_weights["exemplary"] + 1.0
            return (multiplier * self.num_votes,)

        return (self.num_votes,)
