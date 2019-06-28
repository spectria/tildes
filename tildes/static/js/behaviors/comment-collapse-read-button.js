// Copyright (c) 2019 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-comment-collapse-read-button]", function() {
    var commentExpand = function(idx, elem) {
        $(elem).removeClass("is-comment-collapsed");
        $(elem).removeClass("is-comment-collapsed-individual");
    };

    var commentCollapse = function(idx, elem) {
        $(elem).removeClass("is-comment-collapsed-individual");
        $(elem).addClass("is-comment-collapsed");
    };

    var commentCollapseIndividual = function(idx, elem) {
        $(elem).removeClass("is-comment-collapsed");
        $(elem).addClass("is-comment-collapsed-individual");
    };

    $(this).click(function() {
        // expand all comments to start with consistent state
        $(".is-comment-collapsed, .is-comment-collapsed-individual").each(
            commentExpand
        );

        // fully collapse the "shallowest" comment in a branch with no new descendants
        $(".comment").each(function(idx, elem) {
            if (
                $(elem).parents(".is-comment-collapsed").length === 0 &&
                $(elem).find(".is-comment-new").length === 0
            )
                $(elem).each(commentCollapse);
        });

        // expand new comments
        $(".is-comment-new").each(function(idx, elem) {
            $(elem)
                // expand new comments just in case they were collapsed above
                .each(commentExpand)
                // do the same for their immediate parents
                .parent()
                .closest(".comment")
                .each(commentExpand)
                // individual-collapse all of their ancestors unless they're an
                // immediate parent of a new comment (in the case one new comment
                // responds to another)
                .parents(".comment")
                .each(function(idx2, ancestor) {
                    if (
                        $(ancestor).find(
                            "> .comment-tree > .comment-tree-item > .is-comment-new"
                        ).length === 0
                    )
                        commentCollapseIndividual(idx2, ancestor);
                });
        });

        $(this).blur();
    });
});
