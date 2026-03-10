"""
Add flight use-case.

Adds a flight (origin → destination and return) to a trip by invite code.
Raises ValueError if trip not found or input invalid.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from src.domain.trip import Flight, Trip
from src.ports.repositories import FlightRepository, TripRepository


@dataclass
class AddFlightResult:
    """Result of adding a flight."""

    flight: Flight


class AddFlightService:
    """Adds a flight to a trip by invite code. Single responsibility."""

    def __init__(
        self,
        trip_repo: TripRepository,
        flight_repo: FlightRepository,
    ) -> None:
        self._trip_repo = trip_repo
        self._flight_repo = flight_repo

    def execute(
        self,
        invite_code: str,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date,
        cost_estimate: Decimal,
        departure_time: Optional[str] = None,
        link: Optional[str] = None,
    ) -> AddFlightResult:
        """Add flight to trip. Raises ValueError if trip not found or dates invalid."""
        code = (invite_code or "").strip()
        if not code:
            raise ValueError("Invite code is required")
        origin_clean = (origin or "").strip()
        destination_clean = (destination or "").strip()
        if not origin_clean:
            raise ValueError("Origin is required")
        if not destination_clean:
            raise ValueError("Destination is required")
        if return_date < departure_date:
            raise ValueError("Return date must be on or after departure date")
        if cost_estimate < 0:
            raise ValueError("Cost cannot be negative")

        trip = self._trip_repo.get_by_invite_code(code)
        if trip is None or trip.id is None:
            raise ValueError("Trip not found")

        departure_time_clean = (departure_time or "").strip() or None
        link_clean = (link or "").strip() or None
        flight = Flight(
            id=None,
            trip_id=trip.id,
            origin=origin_clean,
            destination=destination_clean,
            departure_date=departure_date,
            return_date=return_date,
            cost_estimate=cost_estimate,
            departure_time=departure_time_clean,
            link=link_clean,
        )
        saved = self._flight_repo.create(flight)
        return AddFlightResult(flight=saved)
