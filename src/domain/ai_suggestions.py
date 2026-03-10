"""
Domain DTOs for AI-generated suggestions.

These represent options returned by the AI before the user selects one.
They are not persisted until the user chooses (e.g. "Save selected flight").
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class FlightOption:
    """One flight option suggested by AI (not yet saved to trip)."""

    origin: str
    destination: str
    departure_date: date
    return_date: date
    cost_estimate: Decimal
    description: str  # e.g. "United 9:00 AM – 2:00 PM, direct"
    airline: Optional[str] = None
    flight_number: Optional[str] = None
    link: Optional[str] = None


@dataclass
class HotelOption:
    """One hotel option suggested by AI (not yet saved to trip)."""

    name: str
    check_in_date: date
    check_out_date: date
    cost_estimate: Decimal
    description: str  # e.g. "4-star, beachfront, free breakfast"
    link: Optional[str] = None


@dataclass
class ActivitySuggestion:
    """One activity suggested for a day (not yet saved)."""

    title: str
    time: Optional[str]
    cost_estimate: Optional[Decimal]
    description: Optional[str] = None
