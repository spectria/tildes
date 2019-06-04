// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-autoselect-input]", function() {
    $(this).click(function() {
        $(this).select();
    });
});
