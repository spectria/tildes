// Copyright (c) 2019 Tildes contributors <code@tildes.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

$.onmount("[data-js-stripe-checkout]", function() {
    /* eslint-disable-next-line no-undef */
    var stripe = Stripe($(this).attr("data-js-stripe-checkout"));
    stripe.redirectToCheckout({
        sessionId: $(this).attr("data-js-stripe-checkout-session")
    });
});
