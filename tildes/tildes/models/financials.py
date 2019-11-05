# Copyright (c) 2019 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the Financials class."""

from decimal import Decimal

from psycopg2.extras import DateRange
from sqlalchemy import Boolean, Column, Index, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import DATERANGE, ENUM

from tildes.enums import FinancialEntryType
from tildes.models import DatabaseModel


class Financials(DatabaseModel):
    """Model holding information about the site's financials over time."""

    __tablename__ = "financials"

    entry_id: int = Column(Integer, primary_key=True)
    entry_type: FinancialEntryType = Column(ENUM(FinancialEntryType), nullable=False)
    description: str = Column(Text)
    amount: Decimal = Column(Numeric(scale=2), nullable=False)
    date_range: DateRange = Column(DATERANGE, nullable=False)
    is_approximate: bool = Column(Boolean, nullable=False, server_default="false")

    # Add a GiST index on the date_range column for range operators
    __table_args__ = (
        Index("ix_financials_date_range_gist", date_range, postgresql_using="gist"),
    )
