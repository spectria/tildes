// Copyright (c) 2020 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

// Note: unlike almost all other JS behaviors, this one does not attach to elements
// based on the presence of a data-js-* HTML attribute. This attaches to any element
// with the dropdown-toggle class so that this behavior is always applied to dropdowns.
$.onmount(".dropdown-toggle", function() {
    $(this).click(function() {
        var $this = $(this);

        // Spectre.css's dropdown menus use the focus event to display the menu,
        // but Safari and Firefox on OSX don't give focus to a <button> when it's
        // clicked. More info:
        // https://developer.mozilla.org/en-US/docs/Web/HTML/Element/button#Clicking_and_focus
        // This should make the behavior consistent across all browsers
        $this.focus();

        $this.toggleClass("active");

        // If toggleClass removed the class, that means that the click was on an
        // already-active button, so we should hide the menu (via losing focus).
        if (!$this.hasClass("active")) {
            $this.blur();
            return;
        }

        // If the menu ends up off the left edge of the screen, remove the
        // .dropdown-right class so that it's aligned to the left edge of the button
        // instead of the right edge
        var $menu = $this.siblings(".menu").first();
        $this
            .parent()
            .toggleClass(
                "dropdown-right",
                $this.offset().left + $this.outerWidth() - $menu.outerWidth() > 0
            );

        // If the menu extends past the bottom of the viewport, or the site footer
        // overlaps the menu, push the menu above the button instead.
        var menuBottom = $this.offset().top + $this.outerHeight() + $menu.outerHeight();
        var viewportHeight = $(window).height();
        var scrollTop = $(document).scrollTop();
        var footerTop = $("#site-footer").offset().top;
        $this
            .parent()
            .toggleClass(
                "dropdown-bottom",
                menuBottom > viewportHeight + scrollTop || menuBottom > footerTop
            );
    });

    $(this).blur(function() {
        $(this).removeClass("active");
    });
});
