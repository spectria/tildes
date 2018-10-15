# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Contains the ScraperResult class."""

from datetime import datetime
from typing import Any

from sqlalchemy import Column, Integer, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.sql.expression import text

from tildes.enums import ScraperType
from tildes.models import DatabaseModel


class ScraperResult(DatabaseModel):
    """Model for the result from a scraper processing a url."""

    __tablename__ = "scraper_results"

    result_id: int = Column(Integer, primary_key=True)
    url: str = Column(Text, nullable=False, index=True)
    scraper_type: ScraperType = Column(ENUM(ScraperType), nullable=False)
    scrape_time: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        server_default=text("NOW()"),
    )
    data: Any = Column(JSONB(none_as_null=True))

    def __init__(self, url: str, scraper_type: ScraperType, data: Any):
        """Create a new ScraperResult."""
        self.url = url
        self.scraper_type = scraper_type
        self.data = data
