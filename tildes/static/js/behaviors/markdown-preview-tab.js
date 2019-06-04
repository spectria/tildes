// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-markdown-preview-tab]", function() {
    $(this).click(function() {
        var $editTextarea = $(this)
            .closest("form")
            .find('[name="markdown"]');
        var $previewDiv = $(this)
            .closest("form")
            .find(".form-markdown-preview");

        $editTextarea.addClass("d-none");
        $previewDiv.removeClass("d-none");
    });

    $(this).on("after.success.ic success.ic", function(event) {
        // Stop intercooler event from bubbling up past this button. This
        // prevents behaviors on parent elements from mistaking a successful
        // "preview" from a successful "submit".
        event.stopPropagation();
    });
});
