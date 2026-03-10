"""
Mock AI suggestions service.

Returns empty lists. Used when no API key is configured or for testing.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from src.domain.ai_suggestions import ActivitySuggestion, FlightOption, HotelOption


class MockAISuggestionsService:
    """No-op implementation: returns empty lists. No API calls."""

    def get_flight_options(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date,
    ) -> List[FlightOption]:
        return []

    def get_flight_options_custom(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: Optional[date] = None,
        trip_type: str = "roundtrip",
    ) -> List[FlightOption]:
        return []

    def get_hotel_options(
        self,
        destination: str,
        check_in_date: date,
        check_out_date: date,
        budget_hint: Optional[Decimal] = None,
    ) -> List[HotelOption]:
        return []

    def get_activity_suggestions(
        self,
        day_date: date,
        destination: str,
        preferences: str,
        budget_remaining: Optional[Decimal] = None,
    ) -> List[ActivitySuggestion]:
        return []

    def get_trip_suggestions(
        self,
        origin: str,
        destination: str,
        start_date: date,
        end_date: date,
        num_people: int,
        total_budget: Decimal,
    ) -> Tuple[List[FlightOption], List[HotelOption]]:
        return [], []
