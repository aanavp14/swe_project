"""Interfaces for external dependencies (repositories)."""

from src.ports.repositories import (
    ActivityRepository,
    CollaboratorRepository,
    DayRepository,
    FlightRepository,
    HotelRepository,
    TripRepository,
)

__all__ = [
    "ActivityRepository",
    "CollaboratorRepository",
    "DayRepository",
    "FlightRepository",
    "HotelRepository",
    "TripRepository",
]
