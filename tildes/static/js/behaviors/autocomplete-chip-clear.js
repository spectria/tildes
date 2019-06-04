// Copyright (c) 2019 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-autocomplete-chip-clear]", function() {
    function clearChip($chip) {
        var $tagsHiddenInput = $("[data-js-autocomplete-hidden-input]");
        var $autocompleteInput = $("[data-js-autocomplete-input]");

        var textToReplace = new RegExp($chip.text() + ",");
        $tagsHiddenInput.val($tagsHiddenInput.val().replace(textToReplace, ""));
        $chip.remove();
        $autocompleteInput.focus();
    }

    $(this).click(function(event) {
        event.preventDefault();
        clearChip($(this).parent());
    });

    $(this).keydown(function(event) {
        switch (event.key) {
            case "Backspace":
                event.preventDefault();
                clearChip($(this).parent());
                break;
            default:
                break;
        }
    });
});
