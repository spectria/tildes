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

from tildes.metrics import incr_counter
from tildes.views.decorators import rate_limit_view, use_kwargs


@view_config(
    route_name="donate_stripe",
    request_method="GET",
    renderer="donate_stripe.jinja2",
    permission=NO_PERMISSION_REQUIRED,
)
def get_donate_stripe(request: Request) -> dict:
    """Display the form for donating with Stripe."""
    # pylint: disable=unused-argument
    return {}


@view_config(
    route_name="donate_stripe",
    request_method="POST",
    renderer="donate_stripe_redirect.jinja2",
    permission=NO_PERMISSION_REQUIRED,
)
@use_kwargs(
    {
        "amount": Float(required=True, validate=Range(min=1.0)),
        "currency": String(required=True, validate=OneOf(("CAD", "USD"))),
        "interval": String(required=True, validate=OneOf(("onetime", "month", "year"))),
    },
    location="form",
)
@rate_limit_view("global_donate_stripe")
@rate_limit_view("donate_stripe")
def post_donate_stripe(
    request: Request, amount: int, currency: str, interval: str
) -> dict:
    """Process a Stripe donation."""
    try:
        stripe.api_key = request.registry.settings["api_keys.stripe.secret"]
        publishable_key = request.registry.settings["api_keys.stripe.publishable"]
        product_id = request.registry.settings["stripe.recurring_donation_product_id"]
    except KeyError:
        raise HTTPInternalServerError

    incr_counter("donation_initiations", type="stripe")

    if interval == "onetime":
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
            cancel_url="https://docs.tildes.net/donate",
        )
    else:
        product = stripe.Product.retrieve(product_id)
        existing_plans = stripe.Plan.list(product=product, active=True, limit=100)

        # look through existing plans to see if there's already a matching one, or
        # create a new plan if not
        for existing_plan in existing_plans:
            if (
                existing_plan.amount == int(amount * 100)
                and existing_plan.currency == currency.lower()
                and existing_plan.interval == interval
            ):
                plan = existing_plan
                break
        else:
            plan = stripe.Plan.create(
                amount=int(amount * 100),
                currency=currency,
                interval=interval,
                product=product,
            )

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            subscription_data={"items": [{"plan": plan.id}]},
            success_url="https://tildes.net/donate_success",
            cancel_url="https://docs.tildes.net/donate",
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
