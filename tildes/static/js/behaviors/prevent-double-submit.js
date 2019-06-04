// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-prevent-double-submit]", function() {
    /* eslint-disable-next-line no-unused-vars */
    $(this).on("beforeSend.ic", function(evt, elt, data, settings, xhr, requestId) {
        var $form = $(this);

        if ($form.attr("data-js-submitting") !== undefined) {
            xhr.abort();
            return false;
        } else {
            $form.attr("data-js-submitting", true);
        }
    });

    $(this).on("complete.ic", function() {
        $(this).removeAttr("data-js-submitting");
    });
});
