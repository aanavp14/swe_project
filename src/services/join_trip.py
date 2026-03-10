"""
Join trip use-case.

Finds a trip by invite code and adds a collaborator (name + budget).
Raises ValueError if trip not found or input invalid.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from src.domain.trip import Collaborator, Trip
from src.ports.repositories import CollaboratorRepository, TripRepository


@dataclass
class JoinTripResult:
    """Result of joining a trip."""

    collaborator: Collaborator


class JoinTripService:
    """Adds a collaborator to a trip by invite code. Single responsibility."""

    def __init__(
        self,
        trip_repo: TripRepository,
        collaborator_repo: CollaboratorRepository,
    ) -> None:
        self._trip_repo = trip_repo
        self._collaborator_repo = collaborator_repo

    def execute(
        self,
        invite_code: str,
        name: str,
        budget: Decimal,
        user_id: Optional[int] = None,
    ) -> JoinTripResult:
        """
        Join the trip with the given invite code as a new collaborator.
        Raises ValueError if trip not found, name is empty, or budget is negative.
        """
        code = (invite_code or "").strip()
        if not code:
            raise ValueError("Invite code is required")
        name_clean = (name or "").strip()
        if not name_clean:
            raise ValueError("Name is required")
        if budget < 0:
            raise ValueError("Budget cannot be negative")

        trip = self._trip_repo.get_by_invite_code(code)
        if trip is None or trip.id is None:
            raise ValueError("Trip not found")

        collaborator = Collaborator(
            id=None,
            trip_id=trip.id,
            name=name_clean,
            budget=budget,
        )
        saved = self._collaborator_repo.create(collaborator, user_id=user_id)
        return JoinTripResult(collaborator=saved)
