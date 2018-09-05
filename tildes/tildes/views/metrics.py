# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The view for exposing metrics to be picked up by Prometheus."""

from prometheus_client import CollectorRegistry, generate_latest, multiprocess
from pyramid.request import Request
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config


@view_config(route_name="metrics", renderer="string", permission=NO_PERMISSION_REQUIRED)
def get_metrics(request: Request) -> str:
    """Merge together the metrics from all workers and output them."""
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    data = generate_latest(registry)

    # When Prometheus accesses this page it will always create a new session.  This
    # session is useless and will never be used again, so we can just invalidate it to
    # cause it to be deleted from storage. It would be even better to find a way to not
    # create it in the first place.
    request.session.invalidate()

    return data.decode("utf-8")
