// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-auto-focus]", function() {
    var $input = $(this);

    // just calling .focus() will place the cursor at the start of the field,
    // so un-setting and re-setting the value moves the cursor to the end
    var original_val = $input.val();
    $input
        .focus()
        .val("")
        .val(original_val);
});
