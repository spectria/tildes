// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-sidebar-toggle]", function() {
    $(this).click(function(event) {
        event.preventDefault();
        event.stopPropagation();

        $("#sidebar").toggleClass("is-sidebar-displayed");
    });
});
