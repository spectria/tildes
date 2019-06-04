// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-tab]", function() {
    $(this).click(function() {
        $(this)
            .siblings()
            .removeClass("active");
        $(this).addClass("active");
    });
});
