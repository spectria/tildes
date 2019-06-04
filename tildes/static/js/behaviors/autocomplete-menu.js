// Copyright (c) 2019 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-autocomplete-menu]", function() {
    var $autocompleteContainer = $(this)
        .parents("[data-js-autocomplete-container]")
        .first();
    var $chips = $autocompleteContainer.find("[data-js-autocomplete-chips]").first();

    $(this)
        .children("[data-js-autocomplete-menu-item]")
        .each(function(index, $menuItem) {
            $menuItem.setAttribute("tabindex", $chips.children().length + index);
        });
});
