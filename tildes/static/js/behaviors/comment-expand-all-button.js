// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-comment-expand-all-button]", function() {
    $(this).click(function() {
        $(".is-comment-collapsed, .is-comment-collapsed-individual").each(function(
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
