// Copyright (c) 2019 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-autocomplete-menu-item]", function() {
    function addChip($menuItem) {
        var $autocompleteContainer = $menuItem
            .parents("[data-js-autocomplete-container]")
            .first();
        var $clickedSuggestion = $menuItem.find(".tile > .tile-content").first();
        var clickedSuggestionText = $clickedSuggestion.html().trim();
        var $tagsHiddenInput = $("[data-js-autocomplete-hidden-input]");
        var $autocompleteInput = $("[data-js-autocomplete-input]");

        if (!$tagsHiddenInput.val().includes(clickedSuggestionText + ",")) {
            var $chips = $autocompleteContainer
                .find("[data-js-autocomplete-chips]")
                .first();

            var clearIcon = document.createElement("a");
            clearIcon.classList.add("btn");
            clearIcon.classList.add("btn-clear");
            clearIcon.setAttribute("data-js-autocomplete-chip-clear", "");
            clearIcon.setAttribute("aria-label", "Close");
            clearIcon.setAttribute("role", "button");
            clearIcon.setAttribute("tabindex", $chips.children().length);

            var $chip = $(document.createElement("div"));
            $chip.addClass("chip");
            $chip.html(clickedSuggestionText);
            $chip.append(clearIcon);

            $chips.append($chip);

            $tagsHiddenInput.val($tagsHiddenInput.val() + clickedSuggestionText + ",");
        }

        $autocompleteContainer.find("[data-js-autocomplete-input]").val("");
        $autocompleteContainer.find("[data-js-autocomplete-suggestions]").html("");
        $autocompleteInput.focus();

        $.onmount();
    }

    $(this).click(function(event) {
        event.preventDefault();
        addChip($(this), event);
    });

    $(this).keydown(function(event) {
        var $nextActiveItem = null;
        switch (event.key) {
            case "Escape":
                $("[data-js-autocomplete-menu]")
                    .parent()
                    .remove();
                break;
            case "Enter":
                event.preventDefault();
                addChip($(this));
                break;
            case "ArrowDown":
                event.preventDefault();
                $nextActiveItem = $(this)
                    .parent()
                    .next();
                $nextActiveItem
                    .children("[data-js-autocomplete-menu-item]")
                    .first()
                    .focus();
                break;
            case "ArrowUp":
                event.preventDefault();
                $nextActiveItem = $(this)
                    .parent()
                    .prev();
                $nextActiveItem
                    .children("[data-js-autocomplete-menu-item]")
                    .first()
                    .focus();
                break;
            default:
                break;
        }
    });
});
