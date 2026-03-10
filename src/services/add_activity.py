"""
Add activity use-case.

Adds an activity to a day within a trip.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from src.domain.trip import Activity, Day
from src.ports.repositories import ActivityRepository, DayRepository, TripRepository


@dataclass
class AddActivityResult:
    """Result of adding an activity."""

    activity: Activity


class AddActivityService:
    """Add an activity to a trip day."""

    def __init__(
        self,
        trip_repo: TripRepository,
        day_repo: DayRepository,
        activity_repo: ActivityRepository,
    ) -> None:
        self._trip_repo = trip_repo
        self._day_repo = day_repo
        self._activity_repo = activity_repo

    def execute(
        self,
        invite_code: str,
        day_id: int,
        title: str,
        time: Optional[str] = None,
        cost_estimate: Optional[Decimal] = None,
    ) -> Optional[AddActivityResult]:
        """Add activity to the given day. Returns None if trip/day not found."""
        trip = self._trip_repo.get_by_invite_code(invite_code)
        if trip is None or trip.id is None:
            return None
        days = self._day_repo.get_by_trip_id(trip.id)
        day = next((d for d in days if d.id == day_id), None)
        if day is None:
            return None
        existing = self._activity_repo.get_by_day_id(day_id)
        order = max((a.order for a in existing), default=-1) + 1
        activity = Activity(
            id=None,
            day_id=day_id,
            title=title.strip(),
            time=time.strip() if time else None,
            cost_estimate=cost_estimate,
            order=order,
        )
        activity = self._activity_repo.create(activity)
        return AddActivityResult(activity=activity)
