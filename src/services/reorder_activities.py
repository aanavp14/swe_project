"""
Reorder activities use-case.

Updates the order of activities within a day. Expects activity_ids in the desired order.
"""

from src.ports.repositories import ActivityRepository, DayRepository, TripRepository


class ReorderActivitiesService:
    """Reorders activities in a day by invite code and activity id list."""

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
        activity_ids: list[int],
    ) -> None:
        """
        Reorder activities in the given day. activity_ids must contain all activities
        for that day in the new order. Raises ValueError if trip/day not found or
        activity_ids don't match the day's activities.
        """
        code = (invite_code or "").strip()
        if not code:
            raise ValueError("Invite code is required")

        trip = self._trip_repo.get_by_invite_code(code)
        if trip is None or trip.id is None:
            raise ValueError("Trip not found")

        days = self._day_repo.get_by_trip_id(trip.id)
        day_ids = {d.id for d in days}
        if day_id not in day_ids:
            raise ValueError("Day not found")

        existing = self._activity_repo.get_by_day_id(day_id)
        existing_ids = {a.id for a in existing if a.id is not None}
        requested_ids = set(activity_ids)

        if requested_ids != existing_ids:
            raise ValueError("activity_ids must match all activities in the day")

        for order, aid in enumerate(activity_ids):
            self._activity_repo.update_order(aid, order)
