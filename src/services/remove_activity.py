"""
Remove activity use-case.

Deletes an activity from a trip by invite code + activity id.
"""

from dataclasses import dataclass

from src.ports.repositories import ActivityRepository, TripRepository


@dataclass
class RemoveActivityResult:
    """Result of removing an activity."""

    removed: bool


class RemoveActivityService:
    """Remove an activity from a trip by invite code."""

    def __init__(self, trip_repo: TripRepository, activity_repo: ActivityRepository) -> None:
        self._trip_repo = trip_repo
        self._activity_repo = activity_repo

    def execute(self, invite_code: str, activity_id: int) -> RemoveActivityResult:
        code = (invite_code or "").strip()
        if not code:
            raise ValueError("Invite code is required")
        trip = self._trip_repo.get_by_invite_code(code)
        if trip is None or trip.id is None:
            raise ValueError("Trip not found")
        activities = self._activity_repo.get_by_trip_id(trip.id)
        if not any(a.id == activity_id for a in activities):
            raise ValueError("Activity not found")
        return RemoveActivityResult(removed=self._activity_repo.delete_by_id(activity_id))
