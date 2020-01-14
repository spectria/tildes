// Copyright (c) 2020 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

// Note: unlike almost all other JS behaviors, this one does not attach to elements
// based on the presence of a data-js-* HTML attribute. This attaches to any element
// with the dropdown-toggle class so that this behavior is always applied to dropdowns.
$.onmount(".dropdown-toggle", function() {
    $(this).click(function() {
        // Spectre.css's dropdown menus use the focus event to display the menu,
        // but Safari and Firefox on OSX don't give focus to a <button> when it's
        // clicked. More info:
        // https://developer.mozilla.org/en-US/docs/Web/HTML/Element/button#Clicking_and_focus
        // This should make the behavior consistent across all browsers
        $(this).focus();

        $(this).toggleClass("active");

        // If toggleClass removed the class, that means that the click was on an
        // already-active button, so we should hide the menu (via losing focus).
        if (!$(this).hasClass("active")) {
            $(this).blur();
        }
    });

    $(this).blur(function() {
        $(this).removeClass("active");
    });
});
