// Copyright (c) 2019 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-theme-preview]", function() {
    $(this).click(function() {
        var newTheme = $(this).attr("data-js-theme-preview");

        Tildes.changeTheme(newTheme);
    });
});
