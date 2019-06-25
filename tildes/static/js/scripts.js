// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$(function() {
    $.onmount();

    // Add the CSRF token to all Intercooler AJAX requests as a header
    /* eslint-disable-next-line no-unused-vars */
    $(document).on("beforeAjaxSend.ic", function(event, ajaxSetup, elt) {
        var token = $("meta[name='csrftoken']").attr("content");
        ajaxSetup.headers["X-CSRF-Token"] = token;

        // This is pretty ugly - adds an X-IC-Trigger-Name header for DELETE
        // requests since the POST params are not accessible
        if (ajaxSetup.headers["X-HTTP-Method-Override"] === "DELETE") {
            var re = /ic-trigger-name=(\S+?)(&|$)/;
            var match = re.exec(ajaxSetup.data);
            if (match && match.length > 1) {
                ajaxSetup.headers["X-IC-Trigger-Name"] = match[1];
            }
        }
    });

    // Automatically call onmount whenever Intercooler swaps in new content
    Intercooler.ready(function() {
        $.onmount();
    });

    // Called whenever an Intercooler request completes; used for <form> elements
    // to display the error or a success message.
    // If the triggering element already contains an element with class
    // "form-status", it will be removed, then a new one is added inside the
    // .form-buttons element if possible, otherwise it will be appended to the
    // triggering element itself. The status div will then have its class set based
    // on whether the response was an error or not, and the text set to either the
    // error message or a generic success message.
    /* eslint-disable-next-line no-unused-vars */
    $(document).on("complete.ic", function(evt, elt, data, status, xhr, requestId) {
        // only do anything for <form> elements
        if (elt[0].tagName !== "FORM") {
            return;
        }

        // see if a status element already exists and remove it
        $(elt)
            .find(".form-status")
            .remove();

        // add a new one (inside .form-buttons if possible)
        var statusDiv = '<div class="form-status"></div>';

        var $buttonElement = $(elt)
            .find(".form-buttons")
            .first();
        if ($buttonElement.length) {
            $buttonElement.append(statusDiv);
        } else {
            $(elt).append(statusDiv);
        }
        var $statusElement = $(elt)
            .find(".form-status")
            .first();

        // set the class and text, then fade in
        $statusElement.hide();
        if (status === "success") {
            $statusElement.addClass("form-status-success").text("Saved successfully");
        } else {
            var errorText = xhr.responseText;
            if (xhr.status === 413) {
                errorText = "Too much data submitted";
            }

            // check if the response came back as HTML (unhandled error of some sort)
            if (errorText.lastIndexOf("<html>", 500) !== -1) {
                errorText = "Unknown error";
            }

            $statusElement.addClass("form-status-error").text(errorText);
        }
        $statusElement.fadeIn("slow");
    });
});

// Create a namespacing object to hold functions
if (!window.Tildes) {
    window.Tildes = {};
}
