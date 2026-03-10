"""
Remove flight use-case.

Deletes a flight from a trip by invite code + flight id.
"""

from dataclasses import dataclass

from src.ports.repositories import FlightRepository, TripRepository


@dataclass
class RemoveFlightResult:
    """Result of removing a flight."""

    removed: bool


class RemoveFlightService:
    """Remove a flight from a trip by invite code."""

    def __init__(self, trip_repo: TripRepository, flight_repo: FlightRepository) -> None:
        self._trip_repo = trip_repo
        self._flight_repo = flight_repo

    def execute(self, invite_code: str, flight_id: int) -> RemoveFlightResult:
        code = (invite_code or "").strip()
        if not code:
            raise ValueError("Invite code is required")
        trip = self._trip_repo.get_by_invite_code(code)
        if trip is None or trip.id is None:
            raise ValueError("Trip not found")
        flights = self._flight_repo.get_by_trip_id(trip.id)
        if not any(f.id == flight_id for f in flights):
            raise ValueError("Flight not found")
        return RemoveFlightResult(removed=self._flight_repo.delete_by_id(flight_id))
