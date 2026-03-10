"""
Repository interfaces (ports).

Services depend on these abstractions, not on SQLite or Flask. This allows
testing with in-memory mocks and swapping DB implementations.
"""

from typing import Optional, Protocol

from src.domain.trip import Activity, Collaborator, Day, Flight, Hotel, Trip


class TripRepository(Protocol):
    """Interface for trip persistence."""

    def create(self, trip: Trip) -> Trip:
        """Persist a trip and return it with id set."""
        ...

    def get_by_invite_code(self, code: str) -> Optional[Trip]:
        """Return the trip with the given invite code, or None."""
        ...

    def update_description(self, invite_code: str, description: Optional[str]) -> Optional[Trip]:
        """Update trip description by invite code. Returns updated trip or None."""
        ...


class DayRepository(Protocol):
    """Interface for day persistence."""

    def create(self, day: Day) -> Day:
        """Persist a day and return it with id set."""
        ...

    def get_by_trip_id(self, trip_id: int) -> list[Day]:
        """Return all days for a trip, ordered by order."""
        ...


class CollaboratorRepository(Protocol):
    """Interface for collaborator persistence."""

    def create(self, collaborator: Collaborator, user_id: Optional[int] = None) -> Collaborator:
        """Persist a collaborator and return it with id set."""
        ...

    def get_by_trip_id(self, trip_id: int) -> list[Collaborator]:
        """Return all collaborators for a trip."""
        ...

    def get_by_trip_id_and_user_id(self, trip_id: int, user_id: int) -> Optional[Collaborator]:
        """Return collaborator for trip and user, or None."""
        ...

    def delete_by_id(self, collaborator_id: int) -> bool:
        """Delete one collaborator by id. Returns True if deleted."""
        ...


class FlightRepository(Protocol):
    """Interface for flight persistence."""

    def create(self, flight: Flight) -> Flight:
        """Persist a flight and return it with id set."""
        ...

    def get_by_trip_id(self, trip_id: int) -> list[Flight]:
        """Return all flights for a trip."""
        ...

    def delete_by_id(self, flight_id: int) -> bool:
        """Delete one flight by id. Returns True if deleted."""
        ...


class HotelRepository(Protocol):
    """Interface for hotel persistence."""

    def create(self, hotel: Hotel) -> Hotel:
        """Persist a hotel and return it with id set."""
        ...

    def get_by_trip_id(self, trip_id: int) -> list[Hotel]:
        """Return all hotels for a trip."""
        ...

    def delete_by_id(self, hotel_id: int) -> bool:
        """Delete one hotel by id. Returns True if deleted."""
        ...


class ActivityRepository(Protocol):
    """Interface for activity persistence."""

    def create(self, activity: Activity) -> Activity:
        """Persist an activity and return it with id set."""
        ...

    def get_by_id(self, activity_id: int) -> Optional[Activity]:
        """Return activity by id, or None."""
        ...

    def get_by_day_id(self, day_id: int) -> list[Activity]:
        """Return all activities for a day, ordered by order."""
        ...

    def get_by_trip_id(self, trip_id: int) -> list[Activity]:
        """Return all activities for a trip (all days), ordered by day then order."""
        ...

    def delete_by_id(self, activity_id: int) -> bool:
        """Delete one activity by id. Returns True if deleted."""
        ...

    def update_order(self, activity_id: int, order: int) -> bool:
        """Update an activity's order. Returns True if updated."""
        ...

    def update_day_and_order(self, activity_id: int, day_id: int, order: int) -> bool:
        """Move activity to a different day and set its order. Returns True if updated."""
        ...
