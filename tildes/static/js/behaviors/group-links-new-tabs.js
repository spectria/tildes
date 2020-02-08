// Copyright (c) 2020 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-group-links-new-tabs]", function() {
    // Open links to groups on Tildes in new tabs
    $(this)
        .find(".link-group")
        .each(function() {
            $(this).attr("target", "_blank");
        });
});
