"""
Create trip use-case.

Orchestrates: generate invite code → save trip → create one Day per date in range.
Accepts origin, destination, per-person budget, num people, dates, activity preferences.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from src.domain.trip import Day, Trip
from src.ports.invite_code import InviteCodeGenerator
from src.ports.repositories import DayRepository, TripRepository


@dataclass
class CreateTripResult:
    """Result of creating a trip."""

    trip: Trip
    days: list[Day]


class CreateTripService:
    """Creates a trip with days for the date range. Single responsibility. No I/O."""

    def __init__(
        self,
        trip_repo: TripRepository,
        day_repo: DayRepository,
        invite_code_generator: InviteCodeGenerator,
    ) -> None:
        self._trip_repo = trip_repo
        self._day_repo = day_repo
        self._invite_code_generator = invite_code_generator

    def execute(
        self,
        origin: str,
        destination: str,
        per_person_budget: Decimal,
        num_people: int,
        start_date: date,
        end_date: date,
        activity_preferences: str,
        name: str = "",
        owner_id: Optional[int] = None,
    ) -> CreateTripResult:
        """Create trip and one day per date in the range."""
        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")
        if num_people < 1:
            raise ValueError("num_people must be at least 1")
        if per_person_budget < 0:
            raise ValueError("per_person_budget cannot be negative")
        origin_clean = (origin or "").strip()
        destination_clean = (destination or "").strip()
        if not origin_clean:
            raise ValueError("origin is required")
        if not destination_clean:
            raise ValueError("destination is required")

        invite_code = self._invite_code_generator.generate()
        trip_name = (name or "").strip() or f"Trip to {destination_clean}"
        trip = Trip(
            id=None,
            name=trip_name,
            origin=origin_clean,
            destination=destination_clean,
            per_person_budget=per_person_budget,
            num_people=num_people,
            start_date=start_date,
            end_date=end_date,
            activity_preferences=(activity_preferences or "").strip(),
            invite_code=invite_code,
        )
        saved_trip = self._trip_repo.create(trip, owner_id=owner_id)
        # Create one Day row for each date in the range
        days: list[Day] = []
        current = start_date
        order = 0
        while current <= end_date:
            day = Day(
                id=None,
                trip_id=saved_trip.id,  # type: ignore[union-attr]
                date=current,
                order=order,
            )
            saved_day = self._day_repo.create(day)
            days.append(saved_day)
            current += timedelta(days=1)
            order += 1
        return CreateTripResult(trip=saved_trip, days=days)
