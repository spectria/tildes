// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-theme-selector]", function() {
    Tildes.toggleSetDefaultThemeButton($(this));

    $(this).change(function(event) {
        event.preventDefault();

        // hide any IC change message
        $(this)
            .parent()
            .find(".text-status-message")
            .hide();

        var new_theme = $(this).val();

        // persist the new theme for the user in their cookie
        document.cookie =
            "theme=" +
            new_theme +
            ";" +
            "path=/;max-age=315360000;secure;domain=" +
            document.location.hostname;

        Tildes.changeTheme(new_theme);
        Tildes.toggleSetDefaultThemeButton($(this));
    });
});

Tildes.toggleSetDefaultThemeButton = function(element) {
    var selected_text = $(element)
        .find("option:selected")
        .text();
    var $setDefaultButton = $("#button-set-default-theme");
    // set visibility of 'Set as account default' button
    if (selected_text.indexOf("account default") === -1) {
        $setDefaultButton.removeClass("d-none");
    } else {
        $setDefaultButton.addClass("d-none");
    }
};
