// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-comment-collapse-all-button]", function() {
    $(this).click(function() {
        // first uncollapse any individually collapsed comments
        $(".is-comment-collapsed-individual").each(function(idx, child) {
            $(child)
                .find("[data-js-comment-collapse-button]:first")
                .trigger("click");
        });

        // then collapse all first-level replies
        $('.comment[data-comment-depth="1"]:not(.is-comment-collapsed)').each(function(
            idx,
            child
        ) {
            $(child)
                .find("[data-js-comment-collapse-button]:first")
                .trigger("click");
        });

        $(this).blur();
    });
});
