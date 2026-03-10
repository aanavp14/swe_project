"""
Move activity use-case.

Moves an activity to a different day (and optionally a specific position).
"""

from src.ports.repositories import ActivityRepository, DayRepository, TripRepository


class MoveActivityService:
    """Moves an activity to a different day."""

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
        activity_id: int,
        day_id: int,
        order: int = 0,
    ) -> None:
        """
        Move activity to a different day. Raises ValueError if trip, day, or
        activity not found, or if day doesn't belong to the trip.
        """
        code = (invite_code or "").strip()
        if not code:
            raise ValueError("Invite code is required")

        trip = self._trip_repo.get_by_invite_code(code)
        if trip is None or trip.id is None:
            raise ValueError("Trip not found")

        activity = self._activity_repo.get_by_id(activity_id)
        if activity is None:
            raise ValueError("Activity not found")

        days = self._day_repo.get_by_trip_id(trip.id)
        day_ids = {d.id for d in days if d.id is not None}
        if day_id not in day_ids:
            raise ValueError("Day not found")

        # Verify activity's current day belongs to this trip
        if activity.day_id not in day_ids:
            raise ValueError("Activity not found")

        self._activity_repo.update_day_and_order(activity_id, day_id, order)
