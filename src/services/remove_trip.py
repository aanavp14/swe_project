"""
Remove trip use-case.

Deletes a trip and all related data.
"""

from src.ports.repositories import TripRepository


class RemoveTripService:
    """Removes a trip by invite code."""

    def __init__(self, trip_repo: TripRepository) -> None:
        self._trip_repo = trip_repo

    def execute(self, invite_code: str) -> bool:
        """
        Delete trip and all related data. Returns True if deleted.
        Raises ValueError if trip not found.
        """
        code = (invite_code or "").strip()
        if not code:
            raise ValueError("Invite code is required")
        trip = self._trip_repo.get_by_invite_code(code)
        if trip is None or trip.id is None:
            raise ValueError("Trip not found")
        return self._trip_repo.delete_by_invite_code(code)
