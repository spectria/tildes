// Copyright (c) 2019 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-autocomplete-input]", function() {
    function addChip($input) {
        var $autocompleteContainer = $input
            .parents("[data-js-autocomplete-container]")
            .first();
        var $chips = $autocompleteContainer
            .find("[data-js-autocomplete-chips]")
            .first();
        var $tagsHiddenInput = $("[data-js-autocomplete-hidden-input]");

        $input
            .val()
            .split(",")
            .map(function(tag) {
                return tag.trim();
            })
            .filter(function(tag) {
                return tag !== "";
            })
            .forEach(function(tag) {
                if (!$tagsHiddenInput.val().match(new RegExp("(^|,)" + tag + ","))) {
                    var clearIcon = document.createElement("a");
                    clearIcon.classList.add("btn");
                    clearIcon.classList.add("btn-clear");
                    clearIcon.setAttribute("data-js-autocomplete-chip-clear", "");
                    clearIcon.setAttribute("aria-label", "Close");
                    clearIcon.setAttribute("role", "button");
                    clearIcon.setAttribute("tabindex", $chips.children().length);

                    var $chip = $(document.createElement("div"));
                    $chip.addClass("chip");
                    $chip.html(tag);
                    $chip.append(clearIcon);

                    $chips.append($chip);

                    $tagsHiddenInput.val($tagsHiddenInput.val() + tag + ",");
                }
            });
        $autocompleteContainer.find("[data-js-autocomplete-input]").val("");
        $autocompleteContainer.find("[data-js-autocomplete-suggestions]").html("");

        $.onmount();
    }

    // initialization (won't repeat on re-mounts because it removes the name attr)
    if ($(this).attr("name")) {
        // move the "tags" name to the hidden input (so the form works without JS)
        $(this).removeAttr("name");
        $("[data-js-autocomplete-hidden-input]").attr("name", "tags");

        // attach an event handler to the form that will add the input's value to
        // the end of the tags list before submitting (to include any tag that's
        // still in the input and wasn't converted to a chip)
        $(this)
            .closest("form")
            /* eslint-disable-next-line no-unused-vars */
            .on("beforeSend.ic", function(evt, elt, data, settings, xhr, requestId) {
                var $autocompleteInput = $(elt)
                    .find("[data-js-autocomplete-input]")
                    .first();
                if (!$autocompleteInput.val()) {
                    return;
                }

                var dataPieces = settings.data.split("&");
                for (var i = 0; i < dataPieces.length; i++) {
                    if (dataPieces[i].indexOf("tags=") === 0) {
                        dataPieces[i] += $autocompleteInput.val();
                        $autocompleteInput.val("");
                        break;
                    }
                }
                settings.data = dataPieces.join("&");
            });
    }

    if ($(this).val() !== "") {
        addChip($(this));
    }

    $(this).focus(function() {
        var $autocompleteContainer = $(this)
            .parents("[data-js-autocomplete-container]")
            .first();
        var $chips = $autocompleteContainer
            .find("[data-js-autocomplete-chips]")
            .first();

        $chips.children().removeClass("active");
    });

    $(this).keydown(function(event) {
        var $autocompleteMenu = $("[data-js-autocomplete-menu]").first();
        var $nextActiveItem = null;

        switch (event.key) {
            case "Escape":
                $("[data-js-autocomplete-menu]").remove();
                $(this).blur();
                break;
            case ",":
            case "Enter":
                event.preventDefault();
                addChip($(this));
                break;
            case "ArrowDown":
                event.preventDefault();
                $nextActiveItem = $autocompleteMenu.children(".menu-item").first();
                $nextActiveItem
                    .children("[data-js-autocomplete-menu-item]")
                    .first()
                    .focus();
                break;
            case "ArrowUp":
                event.preventDefault();
                $nextActiveItem = $autocompleteMenu.children(".menu-item").last();
                $nextActiveItem
                    .children("[data-js-autocomplete-menu-item]")
                    .first()
                    .focus();
                break;
            case "Backspace":
                if ($(this).val() === "") {
                    event.preventDefault();
                    var $autocompleteContainer = $(this)
                        .parents("[data-js-autocomplete-container]")
                        .first();
                    var $chips = $autocompleteContainer
                        .find("[data-js-autocomplete-chips]")
                        .first();
                    var $lastChip = $chips.children().last();

                    if ($lastChip.length) {
                        $(this).blur();
                        if (!$lastChip.hasClass("active")) {
                            $lastChip.addClass("active");
                            $lastChip
                                .children("[data-js-autocomplete-chip-clear]")
                                .first()
                                .focus();
                        }
                    }
                }
                break;
        }
    });

    $(this).keyup(function() {
        var $this = $(this);
        var $autocompleteMenu = $("[data-js-autocomplete-menu]");
        if ($autocompleteMenu) {
            $autocompleteMenu.remove();
        }
        if ($this.val() === "") {
            return;
        }
        var $tagsHiddenInput = $("[data-js-autocomplete-hidden-input]");
        var suggestions = $this
            .data("js-autocomplete-input")
            .filter(function(suggestion) {
                return (
                    suggestion.startsWith($this.val().toLowerCase()) &&
                    !$tagsHiddenInput
                        .val()
                        .match(new RegExp("(^|,)" + suggestion + ","))
                );
            });
        if (suggestions.length === 0) {
            return;
        }
        var $autocompleteSuggestions = $("[data-js-autocomplete-suggestions]");
        $autocompleteMenu = $('<ol class="menu" data-js-autocomplete-menu>');

        suggestions.forEach(function(suggestion) {
            $autocompleteMenu.append(
                '<li class="menu-item">' +
                    '<a href="#" data-js-autocomplete-menu-item>' +
                    '<div class="tile tile-centered">' +
                    '<div class="tile-content">' +
                    suggestion +
                    "</div>" +
                    "</div>" +
                    "</a>" +
                    "</li>"
            );
        });
        $autocompleteSuggestions.append($autocompleteMenu);
        $.onmount();
    });
});
