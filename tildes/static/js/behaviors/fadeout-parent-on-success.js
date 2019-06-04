// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-fadeout-parent-on-success]", function() {
    $(this).on("after.success.ic", function() {
        $(this)
            .parent()
            .fadeOut("fast");
    });
});
