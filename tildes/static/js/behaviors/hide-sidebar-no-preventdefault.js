// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-hide-sidebar-no-preventdefault]", function() {
    $(this).on("click", function() {
        $("#sidebar").removeClass("is-sidebar-displayed");
    });
});
