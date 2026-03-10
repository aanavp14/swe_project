"""
Interface for AI-powered suggestions.

Services depend on this abstraction. Implementations can use OpenAI, Anthropic, etc.
A mock implementation returns empty lists when no API key is configured.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Protocol, Tuple

from src.domain.ai_suggestions import ActivitySuggestion, FlightOption, HotelOption


class AISuggestionsService(Protocol):
    """Generate flight, hotel, and activity suggestions via an AI provider."""

    def get_flight_options(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date,
    ) -> List[FlightOption]:
        """Return multiple flight options for the given route and dates."""
        ...

    def get_hotel_options(
        self,
        destination: str,
        check_in_date: date,
        check_out_date: date,
        budget_hint: Optional[Decimal] = None,
    ) -> List[HotelOption]:
        """Return multiple hotel options for the destination and dates."""
        ...

    def get_activity_suggestions(
        self,
        day_date: date,
        destination: str,
        preferences: str,
        budget_remaining: Optional[Decimal] = None,
    ) -> List[ActivitySuggestion]:
        """Return activity suggestions for a single day."""
        ...

    def get_trip_suggestions(
        self,
        origin: str,
        destination: str,
        start_date: date,
        end_date: date,
        num_people: int,
        total_budget: Decimal,
    ) -> Tuple[List[FlightOption], List[HotelOption]]:
        """Search web for flight and hotel options; return both. Uses real search when available."""
        ...
