// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$(function() {
    $.onmount();

    // Add the CSRF token to all Intercooler AJAX requests as a header
    /* eslint-disable-next-line no-unused-vars */
    $(document).on("beforeAjaxSend.ic", function(event, ajaxSetup, elt) {
        var token = $("meta[name='csrftoken']").attr("content");
        ajaxSetup.headers["X-CSRF-Token"] = token;

        // Remove the ic-current-url param - we aren't using it, and there are some
        // overzealous content blockers reacting to phrases like "_show_ads_" in it.
        // All browsers that don't support this API also don't have content blockers
        if ("URLSearchParams" in window) {
            var params = new URLSearchParams(ajaxSetup.data);
            params.delete("ic-current-url");
            ajaxSetup.data = params.toString();
        }

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

    // Called whenever an Intercooler request completes; used to display an error or
    // success message in an appropriate place near supported elements.
    /* eslint-disable-next-line no-unused-vars */
    $(document).on("complete.ic", function(evt, elt, data, status, xhr, requestId) {
        var $container = null;

        // Only display these messages if the triggering element was <form> or <button>
        if (elt[0].tagName === "FORM") {
            $container = $(elt);

            // add the message inside .form-buttons if possible
            var $buttonElement = $container.find(".form-buttons").first();
            if ($buttonElement.length) {
                $container = $buttonElement;
            }
        } else if (elt[0].tagName === "BUTTON") {
            // for buttons, we only want to display error messages
            if (status !== "error") {
                return;
            }

            // choose the containing <menu> as the place to display the message
            // if the button isn't in a menu, nothing will be displayed
            $container = $(elt).closest("menu");
        }

        // exit if it's an unsupported element or no appropriate container was found
        if (!$container || !$container.length) {
            return;
        }

        // see if a status element already exists and remove it
        $container.find(".text-status-message").remove();

        // add the new one
        $container.append('<div class="text-status-message"></div>');
        var $statusElement = $container.find(".text-status-message").first();

        // set the text (and class for errors), then fade in
        $statusElement.hide();
        if (status === "success") {
            $statusElement.text("Saved successfully");
        } else {
            var errorText = xhr.responseText;
            if (xhr.status === 413) {
                errorText = "Too much data submitted";
            }

            // check if the response came back as HTML (unhandled error of some sort)
            if (errorText.lastIndexOf("<html>", 500) !== -1) {
                errorText = "Unknown error";
            }

            $statusElement.addClass("text-error").text(errorText);
        }
        $statusElement.fadeIn("slow");
    });
});

// Create a namespacing object to hold functions
if (!window.Tildes) {
    window.Tildes = {};
}

Tildes.changeTheme = function(newThemeName) {
    // remove any theme classes currently on the body
    var $body = $("body").first();
    var bodyClasses = $body[0].className.split(" ");
    for (var i = 0; i < bodyClasses.length; i++) {
        var cls = bodyClasses[i];
        if (cls.indexOf("theme-") === 0) {
            $body.removeClass(cls);
        }
    }

    // add the class for the new theme to the body
    $body.addClass("theme-" + newThemeName);
};
