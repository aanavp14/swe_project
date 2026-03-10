"""
Domain entities for trips and itineraries.

These are plain data containers (no Flask, no DB). Services and repositories
convert between these and DB models. Keeps domain logic independent of I/O.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class Trip:
    """A vacation trip: origin, destination, budget, dates, preferences."""

    id: Optional[int]  # None until saved to DB
    name: str
    origin: str
    destination: str
    per_person_budget: Decimal
    num_people: int
    start_date: date
    end_date: date
    activity_preferences: str
    invite_code: str
    description: Optional[str] = None

    def total_days(self) -> int:
        """Return the number of days in the trip (inclusive)."""
        return (self.end_date - self.start_date).days + 1

    def total_budget(self) -> Decimal:
        """Return total budget (per_person_budget × num_people)."""
        return self.per_person_budget * self.num_people


@dataclass
class Day:
    """One day in a trip."""

    id: Optional[int]
    trip_id: int
    date: date
    order: int


@dataclass
class Activity:
    """One activity in a day (title, time, cost)."""

    id: Optional[int]
    day_id: int
    title: str
    time: Optional[str]
    cost_estimate: Optional[Decimal]
    order: int


@dataclass
class Collaborator:
    """One person on a trip (name and budget)."""

    id: Optional[int]
    trip_id: int
    name: str
    budget: Decimal


@dataclass
class Flight:
    """Outbound and return flight for a trip (origin → destination and back)."""

    id: Optional[int]
    trip_id: int
    origin: str
    destination: str
    departure_date: date
    return_date: date
    cost_estimate: Decimal
    departure_time: Optional[str] = None
    link: Optional[str] = None


@dataclass
class Hotel:
    """Hotel stay for a trip."""

    id: Optional[int]
    trip_id: int
    name: str
    check_in_date: date
    check_out_date: date
    cost_estimate: Decimal
    link: Optional[str] = None
