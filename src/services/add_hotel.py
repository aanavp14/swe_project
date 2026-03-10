"""
Add hotel use-case.

Adds a hotel stay to a trip by invite code.
Raises ValueError if trip not found or input invalid.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from src.domain.trip import Hotel, Trip
from src.ports.repositories import HotelRepository, TripRepository


@dataclass
class AddHotelResult:
    """Result of adding a hotel."""

    hotel: Hotel


class AddHotelService:
    """Adds a hotel to a trip by invite code. Single responsibility."""

    def __init__(
        self,
        trip_repo: TripRepository,
        hotel_repo: HotelRepository,
    ) -> None:
        self._trip_repo = trip_repo
        self._hotel_repo = hotel_repo

    def execute(
        self,
        invite_code: str,
        name: str,
        check_in_date: date,
        check_out_date: date,
        cost_estimate: Decimal,
        link: Optional[str] = None,
    ) -> AddHotelResult:
        """Add hotel to trip. Raises ValueError if trip not found or dates invalid."""
        code = (invite_code or "").strip()
        if not code:
            raise ValueError("Invite code is required")
        name_clean = (name or "").strip()
        if not name_clean:
            raise ValueError("Hotel name is required")
        if check_out_date <= check_in_date:
            raise ValueError("Check-out date must be after check-in date")
        if cost_estimate < 0:
            raise ValueError("Cost cannot be negative")

        trip = self._trip_repo.get_by_invite_code(code)
        if trip is None or trip.id is None:
            raise ValueError("Trip not found")

        link_clean = (link or "").strip() or None
        hotel = Hotel(
            id=None,
            trip_id=trip.id,
            name=name_clean,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            cost_estimate=cost_estimate,
            link=link_clean,
        )
        saved = self._hotel_repo.create(hotel)
        return AddHotelResult(hotel=saved)
