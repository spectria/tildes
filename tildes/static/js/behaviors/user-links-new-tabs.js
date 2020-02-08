// Copyright (c) 2020 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-user-links-new-tabs]", function() {
    // Open links to users on Tildes in new tabs
    $(this)
        .find(".link-user")
        .each(function() {
            $(this).attr("target", "_blank");
        });
});
