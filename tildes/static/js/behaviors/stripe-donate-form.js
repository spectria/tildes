// Copyright (c) 2019 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-stripe-donate-form]", function() {
    $(this).on("submit", function(event) {
        var $amountInput = $(this).find("#amount");
        var amount = $amountInput.val();

        var $errorDiv = $(this).find(".text-status-message");

        // remove dollar sign and/or comma, then parse into float
        amount = amount.replace(/[$,]/g, "");
        amount = parseFloat(amount);

        if (isNaN(amount)) {
            $errorDiv.text("Please enter a valid dollar amount.");
            event.preventDefault();
            return;
        } else if (amount < 1.0) {
            $errorDiv.text("Donation amount must be at least $1.");
            event.preventDefault();
            return;
        }

        // set the value in case any of the replacements happened
        $amountInput.val(amount);
    });
});
