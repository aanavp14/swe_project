"""Update trip description by invite code."""

from dataclasses import dataclass
from typing import Optional

from src.domain.trip import Trip
from src.ports.repositories import TripRepository


@dataclass
class UpdateTripDescriptionResult:
    """Result of updating trip description."""

    trip: Trip


class UpdateTripDescriptionService:
    """Updates a trip's description by invite code."""

    def __init__(self, trip_repo: TripRepository) -> None:
        self._trip_repo = trip_repo

    def execute(self, invite_code: str, description: Optional[str]) -> Optional[UpdateTripDescriptionResult]:
        """Update trip description. Returns None if trip not found."""
        trip = self._trip_repo.update_description(invite_code, (description or "").strip() or None)
        if trip is None:
            return None
        return UpdateTripDescriptionResult(trip=trip)
