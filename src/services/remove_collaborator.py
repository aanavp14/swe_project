"""
Remove collaborator use-case.

Deletes a collaborator (trip member) from a trip by invite code + collaborator id.
"""

from dataclasses import dataclass

from src.ports.repositories import CollaboratorRepository, TripRepository


@dataclass
class RemoveCollaboratorResult:
    """Result of removing a collaborator."""

    removed: bool


class RemoveCollaboratorService:
    """Remove a collaborator from a trip by invite code."""

    def __init__(
        self,
        trip_repo: TripRepository,
        collaborator_repo: CollaboratorRepository,
    ) -> None:
        self._trip_repo = trip_repo
        self._collaborator_repo = collaborator_repo

    def execute(self, invite_code: str, collaborator_id: int) -> RemoveCollaboratorResult:
        code = (invite_code or "").strip()
        if not code:
            raise ValueError("Invite code is required")
        trip = self._trip_repo.get_by_invite_code(code)
        if trip is None or trip.id is None:
            raise ValueError("Trip not found")
        collaborators = self._collaborator_repo.get_by_trip_id(trip.id)
        if not any(c.id == collaborator_id for c in collaborators):
            raise ValueError("Collaborator not found")
        return RemoveCollaboratorResult(
            removed=self._collaborator_repo.delete_by_id(collaborator_id)
        )
