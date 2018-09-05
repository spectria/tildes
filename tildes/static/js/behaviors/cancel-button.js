// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount('[data-js-cancel-button]', function() {
    $(this).click(function(event) {
        var $parentForm = $(this).closest('form');

        // confirm removal if the form specifies to
        var confirmPrompt = $parentForm.attr('data-js-confirm-cancel');
        if (confirmPrompt) {
            // only prompt if any of the inputs aren't empty
            $nonEmptyFields = $parentForm.find('input,textarea')
                .filter(function() { return $(this).val(); });

            if ($nonEmptyFields.length > 0) {
                var shouldRemove = window.confirm(confirmPrompt);
            } else {
                var shouldRemove = true;
            }
        } else {
            var shouldRemove = true;
        }

        if (shouldRemove) {
            $(this).closest('form').remove();
        }
    });
});
