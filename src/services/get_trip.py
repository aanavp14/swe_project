"""
Get trip use-case.

Loads a trip, its days, and collaborators by invite code. Returns None if not found.
Used by the trip page (/trip/<code>) and the JSON API (/api/trips/<code>).
"""

from dataclasses import dataclass
from typing import Optional

from src.domain.trip import Activity, Collaborator, Day, Flight, Hotel, Trip
from src.ports.repositories import (
    ActivityRepository,
    CollaboratorRepository,
    DayRepository,
    FlightRepository,
    HotelRepository,
    TripRepository,
)


@dataclass
class GetTripResult:
    """Result of loading a trip."""

    trip: Trip
    days: list[Day]
    collaborators: list[Collaborator]
    flights: list[Flight]
    hotels: list[Hotel]
    activities: list[Activity]


class GetTripService:
    """Loads a trip by invite code (with days, collaborators, flights, hotels, activities)."""

    def __init__(
        self,
        trip_repo: TripRepository,
        day_repo: DayRepository,
        collaborator_repo: CollaboratorRepository,
        flight_repo: FlightRepository,
        hotel_repo: HotelRepository,
        activity_repo: ActivityRepository,
    ) -> None:
        self._trip_repo = trip_repo
        self._day_repo = day_repo
        self._collaborator_repo = collaborator_repo
        self._flight_repo = flight_repo
        self._hotel_repo = hotel_repo
        self._activity_repo = activity_repo

    def execute(self, invite_code: str) -> Optional[GetTripResult]:
        """Return trip, days, collaborators, flights, hotels, and activities if found, else None."""
        trip = self._trip_repo.get_by_invite_code(invite_code)
        if trip is None or trip.id is None:
            return None
        days = self._day_repo.get_by_trip_id(trip.id)
        collaborators = self._collaborator_repo.get_by_trip_id(trip.id)
        flights = self._flight_repo.get_by_trip_id(trip.id)
        hotels = self._hotel_repo.get_by_trip_id(trip.id)
        activities = self._activity_repo.get_by_trip_id(trip.id)
        return GetTripResult(
            trip=trip,
            days=days,
            collaborators=collaborators,
            flights=flights,
            hotels=hotels,
            activities=activities,
        )
