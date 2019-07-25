# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The view for donating via Stripe."""

import stripe
from marshmallow.fields import Email, Float, String
from marshmallow.validate import OneOf, Range
from pyramid.httpexceptions import HTTPInternalServerError
from pyramid.request import Request
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from webargs.pyramidparser import use_kwargs

from tildes.views.decorators import rate_limit_view


@view_config(
    route_name="donate_stripe",
    request_method="POST",
    renderer="donate_stripe.jinja2",
    permission=NO_PERMISSION_REQUIRED,
    require_csrf=False,
)
@use_kwargs(
    {
        "stripe_token": String(required=True),
        "donator_email": Email(required=True),
        "amount": Float(required=True, validate=Range(min=1.0)),
        "currency": String(required=True, validate=OneOf(("CAD", "USD"))),
    }
)
@rate_limit_view("donate")
def post_donate_stripe(
    request: Request, stripe_token: str, donator_email: str, amount: int, currency: str
) -> dict:
    """Process a Stripe donation."""
    try:
        stripe.api_key = request.registry.settings["api_keys.stripe"]
    except KeyError:
        raise HTTPInternalServerError

    payment_successful = True
    try:
        stripe.Charge.create(
            source=stripe_token,
            amount=int(amount * 100),
            currency=currency,
            receipt_email=donator_email,
            description="One-time donation",
            statement_descriptor="Donation - tildes.net",
        )
    except stripe.error.StripeError:
        payment_successful = False

    return {"payment_successful": payment_successful}
