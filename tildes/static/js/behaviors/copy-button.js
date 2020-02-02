// Copyright (c) 2020 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-copy-button]", function() {
    $(this).click(function(event) {
        event.preventDefault();

        var textToCopy;
        // If there are multiple inputs or textareas in a form with a copy button, you
        // can use `data-js-copy-target="#selector"` to specify which element should
        // get copied for that button. If this isn't defined, whatever input/textarea
        // element jQuery finds first in the form will be copied instead.
        if ($(this).attr("data-js-copy-target")) {
            var $targetField = $($(this).attr("data-js-copy-target"));
            $targetField.select();
            textToCopy = $targetField.val();
        } else {
            var $parentForm = $(this).closest("form");
            var $firstFoundField = $parentForm.find("input,textarea").first();
            $firstFoundField.select();
            textToCopy = $firstFoundField.val();
        }

        Tildes.writeToClipboard(textToCopy);
    });
});

Tildes.writeToClipboard = function(text) {
    // Minimal polyfill for writing to clipboard, by Lucas Garron
    // https://gist.github.com/lgarron/d1dee380f4ed9d825ca7
    return new Promise(function(resolve, reject) {
        var success = false;
        function listener(event) {
            event.clipboardData.setData("text/plain", text);
            event.preventDefault();
            success = true;
        }

        document.addEventListener("copy", listener);
        document.execCommand("copy");
        document.removeEventListener("copy", listener);
        success ? resolve() : reject();
    });
};
