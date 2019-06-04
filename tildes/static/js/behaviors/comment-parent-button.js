// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-comment-parent-button]", function() {
    $(this).click(function() {
        var $comment = $(this)
            .parents(".comment")
            .first();
        var $parentComment = $comment.parents(".comment").first();

        var backButton = document.createElement("a");
        backButton.setAttribute(
            "href",
            "#comment-" + $comment.attr("data-comment-id36")
        );
        backButton.setAttribute("class", "comment-nav-link");
        backButton.setAttribute("data-js-comment-back-button", "");
        backButton.setAttribute("data-js-remove-on-click", "");
        backButton.innerHTML = "[Back]";

        var $parentHeader = $parentComment.find("header").first();

        // remove any existing back button
        $parentHeader.find("[data-js-comment-back-button]").remove();

        $parentHeader.append(backButton);
        $.onmount();
    });
});
