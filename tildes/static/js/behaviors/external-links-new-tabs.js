// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-external-links-new-tabs]", function() {
    // Open external links in topic, comment, and message text in new tabs
    $(this)
        .find("a")
        .each(function() {
            if (this.host !== window.location.host) {
                $(this).attr("target", "_blank");
                $(this).attr("rel", "noopener");
            }
        });
});
