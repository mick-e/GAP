from datetime import datetime
from typing import Optional

from fastapi import Query


class DateRangeFilter:
    def __init__(
        self,
        start_date: Optional[datetime] = Query(
            None, description="Start date (ISO format)"
        ),
        end_date: Optional[datetime] = Query(
            None, description="End date (ISO format)"
        ),
    ):
        self.start_date = start_date
        self.end_date = end_date


class PaginationFilter:
    def __init__(
        self,
        limit: int = Query(50, ge=1, le=200, description="Items per page"),
        offset: int = Query(0, ge=0, description="Items to skip"),
    ):
        self.limit = limit
        self.offset = offset


class SortFilter:
    def __init__(
        self,
        sort_by: Optional[str] = Query(
            None, description="Field to sort by"
        ),
        sort_order: str = Query(
            "desc", pattern="^(asc|desc)$", description="Sort order"
        ),
    ):
        self.sort_by = sort_by
        self.sort_order = sort_order
