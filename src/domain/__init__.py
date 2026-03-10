"""Domain models: Trip, Day, Activity, Collaborator, Flight, Hotel. Plain dataclasses; no I/O."""

from src.domain.trip import Activity, Collaborator, Day, Flight, Hotel, Trip

__all__ = ["Activity", "Collaborator", "Day", "Flight", "Hotel", "Trip"]
