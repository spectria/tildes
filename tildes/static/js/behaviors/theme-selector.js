// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-theme-selector]", function() {
    $(this).change(function(event) {
        event.preventDefault();

        // hide any IC change message
        $(this)
            .parent()
            .find(".form-status")
            .hide();

        var new_theme = $(this).val();
        var selected_text = $(this)
            .find("option:selected")
            .text();
        var $setDefaultButton = $("#button-set-default-theme");

        // persist the new theme for the user in their cookie
        document.cookie =
            "theme=" +
            new_theme +
            ";" +
            "path=/;max-age=315360000;secure;domain=" +
            document.location.hostname;

        // remove any theme classes currently on the body
        var $body = $("body").first();
        var bodyClasses = $body[0].className.split(" ");
        for (var i = 0; i < bodyClasses.length; i++) {
            var cls = bodyClasses[i];
            if (cls.indexOf("theme-") === 0) {
                $body.removeClass(cls);
            }
        }

        // add the class for the new theme to the body
        $body.addClass("theme-" + new_theme);

        // set visibility of 'Set as account default' button
        if (selected_text.indexOf("account default") === -1) {
            $setDefaultButton.removeClass("d-none");
        } else {
            $setDefaultButton.addClass("d-none");
        }
    });
});
