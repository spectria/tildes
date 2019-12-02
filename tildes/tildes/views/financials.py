# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The view for displaying entries in the financials table."""

from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Optional

from pyramid.request import Request
from pyramid.view import view_config
from sqlalchemy import func
from sqlalchemy.orm.session import Session
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

    financial_data = get_financial_data(request.db_session)

    return {
        "entries": entries,
        "current_time": utc_now(),
        "financial_data": financial_data,
    }


def get_financial_data(db_session: Session) -> Optional[Dict[str, Decimal]]:
    """Return financial data used to render the donation goal box."""
    # get the total sum for each entry type in the financials table relevant to today
    financial_totals = (
        db_session.query(Financials.entry_type, func.sum(Financials.amount))
        .filter(Financials.date_range.op("@>")(text("CURRENT_DATE")))
        .group_by(Financials.entry_type)
        .all()
    )

    financial_data = {entry[0].name.lower(): entry[1] for entry in financial_totals}

    # if any of the entry types were missing, the data won't be usable
    if any(key not in financial_data for key in ("expense", "goal", "income")):
        return None

    financial_data["goal_percentage"] = round(
        financial_data["income"] / financial_data["goal"] * 100
    )

    return financial_data
