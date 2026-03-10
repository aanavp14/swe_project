"""
Leave trip use-case.

Removes the current user as a collaborator from a trip.
Raises ValueError if trip not found or user is not a collaborator.
"""

from src.ports.repositories import CollaboratorRepository, TripRepository


class LeaveTripService:
    """Removes the current user from a trip by invite code."""

    def __init__(
        self,
        trip_repo: TripRepository,
        collaborator_repo: CollaboratorRepository,
    ) -> None:
        self._trip_repo = trip_repo
        self._collaborator_repo = collaborator_repo

    def execute(self, invite_code: str, user_id: int) -> None:
        """Leave the trip. Raises ValueError if trip not found or user not a collaborator."""
        code = (invite_code or "").strip()
        if not code:
            raise ValueError("Invite code is required")
        trip = self._trip_repo.get_by_invite_code(code)
        if trip is None or trip.id is None:
            raise ValueError("Trip not found")
        collab = self._collaborator_repo.get_by_trip_id_and_user_id(trip.id, user_id)
        if collab is None or collab.id is None:
            raise ValueError("You are not a member of this trip")
        self._collaborator_repo.delete_by_id(collab.id)
