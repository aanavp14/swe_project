"""
Remove hotel use-case.

Deletes a hotel from a trip by invite code + hotel id.
"""

from dataclasses import dataclass

from src.ports.repositories import HotelRepository, TripRepository


@dataclass
class RemoveHotelResult:
    """Result of removing a hotel."""

    removed: bool


class RemoveHotelService:
    """Remove a hotel from a trip by invite code."""

    def __init__(self, trip_repo: TripRepository, hotel_repo: HotelRepository) -> None:
        self._trip_repo = trip_repo
        self._hotel_repo = hotel_repo

    def execute(self, invite_code: str, hotel_id: int) -> RemoveHotelResult:
        code = (invite_code or "").strip()
        if not code:
            raise ValueError("Invite code is required")
        trip = self._trip_repo.get_by_invite_code(code)
        if trip is None or trip.id is None:
            raise ValueError("Trip not found")
        hotels = self._hotel_repo.get_by_trip_id(trip.id)
        if not any(h.id == hotel_id for h in hotels):
            raise ValueError("Hotel not found")
        return RemoveHotelResult(removed=self._hotel_repo.delete_by_id(hotel_id))
