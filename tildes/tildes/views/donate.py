# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The view for donating via Stripe."""

import stripe
from marshmallow.fields import Float, String
from marshmallow.validate import OneOf, Range
from pyramid.httpexceptions import HTTPInternalServerError
from pyramid.request import Request
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from webargs.pyramidparser import use_kwargs

from tildes.metrics import incr_counter


@view_config(
    route_name="donate_stripe",
    request_method="POST",
    renderer="donate_stripe.jinja2",
    permission=NO_PERMISSION_REQUIRED,
    require_csrf=False,
)
@use_kwargs(
    {
        "amount": Float(required=True, validate=Range(min=1.0)),
        "currency": String(required=True, validate=OneOf(("CAD", "USD"))),
    }
)
def post_donate_stripe(request: Request, amount: int, currency: str) -> dict:
    """Process a Stripe donation."""
    try:
        stripe.api_key = request.registry.settings["api_keys.stripe.secret"]
        publishable_key = request.registry.settings["api_keys.stripe.publishable"]
    except KeyError:
        raise HTTPInternalServerError

    incr_counter("donation_initiations", type="stripe")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "name": "One-time donation - tildes.net",
                "amount": int(amount * 100),
                "currency": currency,
                "quantity": 1,
            }
        ],
        submit_type="donate",
        success_url="https://tildes.net/donate_success",
        cancel_url="https://docs.tildes.net/donate-stripe",
    )

    return {"publishable_key": publishable_key, "session_id": session.id}


@view_config(route_name="donate_success", renderer="donate_success.jinja2")
def get_donate_success(request: Request) -> dict:
    """Display a message after a successful donation."""
    # pylint: disable=unused-argument

    # incrementing this metric on page-load and hard-coding Stripe isn't ideal, but it
    # should do the job for now
    incr_counter("donations", type="stripe")

    return {}
