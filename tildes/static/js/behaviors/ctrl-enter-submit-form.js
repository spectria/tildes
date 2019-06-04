// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-ctrl-enter-submit-form]", function() {
    $(this).keydown(function(event) {
        if (
            (event.ctrlKey || event.metaKey) &&
            (event.keyCode == 13 || event.keyCode == 10)
        ) {
            $(this)
                .closest("form")
                .submit();
        }
    });
});
