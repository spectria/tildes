// Copyright (c) 2018 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-time-period-select]", function() {
    $(this).change(function() {
        var periodValue = this.value;

        if (periodValue === "other") {
            var enteredPeriod = "";
            var validRegex = /^\d+[hd]?$/i;

            // prompt for a time period until they enter a valid one
            while (!validRegex.test(enteredPeriod)) {
                enteredPeriod = prompt(
                    'Enter a custom time period (number of hours, or add a "d" suffix for days):'
                );

                // exit if they specifically cancelled the prompt
                if (enteredPeriod === null) {
                    return false;
                }
            }

            // if it was just a bare number, append "h"
            if (/^\d+$/.test(enteredPeriod)) {
                enteredPeriod += "h";
            }

            // need to add the option to the <select> so it's valid to choose
            $(this).append('<option value="' + enteredPeriod + '">Custom</option>');

            this.value = enteredPeriod;
        }

        this.form.submit();
    });
});
