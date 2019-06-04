// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-comment-collapse-button]", function() {
    $(this).click(function() {
        var $this = $(this);
        var $comment = $this.closest(".comment");

        // if the comment is individually collapsed, just remove that class,
        // otherwise toggle the collapsed state
        if ($comment.hasClass("is-comment-collapsed-individual")) {
            $comment.removeClass("is-comment-collapsed-individual");
        } else {
            $comment.toggleClass("is-comment-collapsed");
        }

        if ($comment.hasClass("is-comment-collapsed")) {
            $this.text("+");
        } else {
            $this.html("&minus;");
        }

        $this.blur();
    });
});
