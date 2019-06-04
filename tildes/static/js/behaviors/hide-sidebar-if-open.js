// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-hide-sidebar-if-open]", function() {
    $(this).on("click", function(event) {
        if ($("#sidebar").hasClass("is-sidebar-displayed")) {
            event.preventDefault();
            event.stopPropagation();
            $("#sidebar").removeClass("is-sidebar-displayed");
        }
    });
});
