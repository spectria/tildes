# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The view for displaying entries in the financials table."""

from collections import defaultdict
from typing import Dict, List

from pyramid.request import Request
from pyramid.view import view_config
from sqlalchemy.sql.expression import text

from tildes.lib.datetime import utc_now
from tildes.models.financials import Financials


@view_config(
    route_name="financials", request_method="GET", renderer="financials.jinja2"
)
def get_financials(request: Request) -> dict:
    """Display the financials page."""
    financial_entries = (
        request.query(Financials)
        .filter(Financials.date_range.op("@>")(text("CURRENT_DATE")))
        .order_by(Financials.entry_id)
        .all()
    )

    # split the entries up by type
    entries: Dict[str, List] = defaultdict(list)
    for entry in financial_entries:
        entries[entry.entry_type.name.lower()].append(entry)

    return {"entries": entries, "current_time": utc_now()}
