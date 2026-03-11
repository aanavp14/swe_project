"""
OpenAI implementation of AI suggestions.

Uses Responses API with web_search tool for real flight/hotel/activity options.
Falls back to Chat Completions (web-search models or standard) if Responses API unavailable.
"""

import json
import logging
import os
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple

from src.domain.ai_suggestions import FlightOption, HotelOption, ActivitySuggestion

log = logging.getLogger(__name__)


def _is_valid_link(link: Optional[str]) -> bool:
    """Return True only if link is a valid https URL."""
    if not link or not isinstance(link, str):
        return False
    s = link.strip().lower()
    return s.startswith("https://") or s.startswith("http://")


def _build_flight_link(
    origin: str, destination: str, dep_date: date, return_date: Optional[date] = None
) -> str:
    orig = origin.replace(" ", "%20")
    dest = destination.replace(" ", "%20")
    base = f"https://www.google.com/travel/flights?q=Flights%20from%20{orig}%20to%20{dest}"
    if return_date and return_date != dep_date:
        return base + f"%20{dep_date.isoformat()}%20to%20{return_date.isoformat()}"
    return base + f"%20on%20{dep_date.isoformat()}"


def _build_hotel_link(destination: str, check_in: date, check_out: date) -> str:
    dest = destination.replace(" ", "%20")
    return (
        f"https://www.google.com/travel/hotels?q=hotels%20in%20{dest}"
        f"%20{check_in.isoformat()}%20to%20{check_out.isoformat()}"
    )


def _extract_json_block(text: str, opener: str = "{", closer: str = "}") -> Optional[str]:
    """Extract the first balanced JSON block from mixed prose+JSON text."""
    start = text.find(opener)
    if start < 0:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


class OpenAISuggestionsService:
    """Generate suggestions using OpenAI with web search when available."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-search-preview")
        # For Responses API: use stronger model for better grounding in search results
        self._responses_model = os.environ.get("OPENAI_SUGGESTIONS_MODEL", "gpt-4o")
        self._search_model = self._model  # for Chat Completions fallback
        self._fallback_model = "gpt-4o-mini"
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self._api_key:
                raise ValueError("OPENAI_API_KEY is not set")
            from openai import OpenAI
            self._client = OpenAI(api_key=self._api_key)
        return self._client

    def _call_with_web_search(self, prompt: str) -> Optional[str]:
        """Call Responses API with explicit web_search tool for real-time data. Fallback to Chat Completions.
        Each call is stateless — single request, no conversation history."""
        client = self._get_client()
        # 1. Try Responses API with web_search (guarantees web search)
        if hasattr(client, "responses") and hasattr(client.responses, "create"):
            for tool_cfg in (
                [{"type": "web_search"}],
                [{"type": "web_search", "filters": {"allowed_domains": ["google.com", "kayak.com", "booking.com", "expedia.com", "skyscanner.com"]}}],
                [{"type": "web_search_preview"}],
            ):
                try:
                    resp = client.responses.create(
                        model=self._responses_model,
                        input=prompt,
                        tools=tool_cfg,
                        temperature=0,
                    )
                    output = getattr(resp, "output", None) or []
                    for item in output:
                        if getattr(item, "type", None) == "message":
                            for c in getattr(item, "content", []) or []:
                                if getattr(c, "type", None) == "output_text":
                                    text = getattr(c, "text", None) or ""
                                    if text.strip():
                                        return text.strip()
                    log.warning("Responses API returned no text")
                except Exception as e:
                    log.warning("Responses API failed: %s", e)
        # 2. Chat Completions — single user message, no conversation history
        try:
            r = client.chat.completions.create(
                model=self._search_model,
                messages=[
                    {"role": "system", "content": "You are a stateless API. Each request is independent. Do not reference any prior requests."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )
            return (r.choices[0].message.content or "").strip()
        except Exception as e:
            log.warning("Search model %s failed, trying fallback: %s", self._search_model, e)
            r = client.chat.completions.create(
                model=self._fallback_model,
                messages=[
                    {"role": "system", "content": "You are a stateless API. Each request is independent. Do not reference any prior requests."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )
            return (r.choices[0].message.content or "").strip()

    def get_trip_suggestions_raw(
        self,
        origin: str,
        destination: str,
        start_date: date,
        end_date: date,
        num_people: int,
        total_budget: Decimal,
    ) -> str:
        """Call the API and return the raw response string (for debugging)."""
        prompt = self._build_trip_prompt(origin, destination, start_date, end_date, num_people, total_budget)
        content = self._call_with_web_search(prompt)
        return content or "(empty response)"

    def _build_trip_prompt(
        self,
        origin: str,
        destination: str,
        start_date: date,
        end_date: date,
        num_people: int,
        total_budget: Decimal,
    ) -> str:
        return f"""Search the web for current flight and hotel options for this trip.
- Flights: {origin} to {destination}, round-trip {start_date.isoformat()} to {end_date.isoformat()}, {num_people} passengers, budget around ${total_budget}
- Hotels: {destination}, check-in {start_date.isoformat()} check-out {end_date.isoformat()}

CRITICAL: You are an automated agent connected directly to a production database.
1. DO NOT return placeholder text like "Check Google Flights for current prices".
2. You MUST perform the web search.
3. You MUST extract real airlines, real flight numbers, real hotels, and real prices.
4. For each flight and hotel, you MUST include the actual clickable URL in "link" that opens that specific search result.
5. If a field is completely missing (like flight number), set it to null. Do NOT use fake numbers.
6. For flights, provide ONLY the actual price per person in USD.
7. For hotels, the `cost_estimate` MUST be the price PER NIGHT in USD.
8. Return up to 3 flights and up to 3 hotels. Each must have a valid "link".
9. Respond with ONLY valid JSON. No explanations, no prose. If search finds no results, return {{"flights":[],"hotels":[]}}.

Return ONLY valid JSON, no prose:
{{
  "flights": [
    {{"airline": "airline or null", "flight_number": "flight number or null", "description": "short summary", "cost_estimate": number (price PER PERSON in USD), "origin_code": "IATA code", "destination_code": "IATA code", "link": "https://... (actual URL to this specific flight)"}}
  ],
  "hotels": [
    {{"name": "hotel name", "description": "short summary", "cost_estimate": number (price PER NIGHT in USD), "link": "https://... (actual URL to this specific hotel)"}}
  ]
}}"""

    def get_trip_suggestions(
        self,
        origin: str,
        destination: str,
        start_date: date,
        end_date: date,
        num_people: int,
        total_budget: Decimal,
    ) -> Tuple[List[FlightOption], List[HotelOption]]:
        """Search web for flight and hotel options; return both."""
        prompt = self._build_trip_prompt(origin, destination, start_date, end_date, num_people, total_budget)
        content = ""
        try:
            content = self._call_with_web_search(prompt)
            if not content:
                log.warning("AI returned empty content for trip suggestions")
                return [], []

            if content.startswith("```"):
                content = re.sub(r"^```\w*\n?", "", content)
                content = re.sub(r"\n?```$", "", content)
            extracted = _extract_json_block(content, "{", "}")
            if extracted:
                content = extracted
            data = json.loads(content)
        except (json.JSONDecodeError, KeyError, IndexError, AttributeError) as e:
            log.warning("Failed to parse AI response as JSON: %s. Content excerpt: %s", e, content[:500] if content else "(empty)")
            return [], []
        except Exception as e:
            log.exception("AI suggestions error: %s", e)
            return [], []

        flights = []
        hotels = []
        for item in (data.get("flights") or [])[:3]:
            try:
                cost = Decimal(str(item.get("cost_estimate", 0)))
                orig = item.get("origin_code", origin)
                dest = item.get("destination_code", destination)
                flights.append(
                    FlightOption(
                        origin=orig,
                        destination=dest,
                        departure_date=start_date,
                        return_date=end_date,
                        cost_estimate=cost,
                        description=item.get("description", ""),
                        airline=item.get("airline"),
                        flight_number=item.get("flight_number"),
                        link=_build_flight_link(orig, dest, start_date, end_date)
                    if not _is_valid_link(item.get("link"))
                    else item.get("link").strip(),
                    )
                )
            except (InvalidOperation, TypeError):
                continue
        for item in (data.get("hotels") or [])[:3]:
            try:
                cost = Decimal(str(item.get("cost_estimate", 0)))
                hotels.append(
                    HotelOption(
                        name=item.get("name", "Hotel"),
                        check_in_date=start_date,
                        check_out_date=end_date,
                        cost_estimate=cost,
                        description=item.get("description", ""),
                        link=_build_hotel_link(destination, start_date, end_date)
                    if not _is_valid_link(item.get("link"))
                    else item.get("link").strip(),
                    )
                )
            except (InvalidOperation, TypeError):
                continue
        return flights, hotels

    def get_flight_options(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date,
    ) -> List[FlightOption]:
        """Search for flights only. Uses one-way when return_date == departure_date."""
        trip_type = "one_way" if return_date == departure_date else "roundtrip"
        return self.get_flight_options_custom(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            trip_type=trip_type,
        )

    def get_flight_options_custom(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: Optional[date] = None,
        trip_type: str = "roundtrip",
    ) -> List[FlightOption]:
        """Search for flights using explicit one-way/round-trip request."""
        trip_kind = "one-way" if trip_type == "one_way" else "round-trip"
        ret_date = return_date or departure_date
        prompt = f"""Search the web for real {trip_kind} flight options.
Route: {origin} to {destination}
Departure date: {departure_date.isoformat()}
Return date: {ret_date.isoformat() if trip_type != "one_way" else "N/A (one-way)"}

CRITICAL: You are an automated agent connected directly to a production database.
1. DO NOT return placeholder text.
2. You MUST perform the web search.
3. You MUST extract real airlines, real flight numbers, and real prices.
4. For each flight, you MUST include the actual clickable URL in "link" that opens that specific search result.

Return ONLY valid JSON array. No explanations, no prose. If search finds no results, return [].
[{{"airline":"...","flight_number":"... or null","description":"...","cost_estimate": number,"origin_code":"...","destination_code":"...","link":"https://... (actual URL to this flight)","trip_type":"{trip_type}"}}]

Rules:
- Include up to 5 options from web search results.
- Each flight must have "link" with a real https:// URL.
- Do not fabricate; use null for flight_number if unavailable. Do NOT use fake numbers.
- Set trip_type exactly to "{trip_type}" for each item."""
        try:
            content = self._call_with_web_search(prompt)
            if not content:
                return []
            if content.startswith("```"):
                content = re.sub(r"^```\w*\n?", "", content)
                content = re.sub(r"\n?```$", "", content)
            extracted = _extract_json_block(content, "[", "]")
            if extracted:
                content = extracted
            data = json.loads(content)
            flights = []
            for item in (data if isinstance(data, list) else [])[:5]:
                try:
                    cost = Decimal(str(item.get("cost_estimate", 0)))
                    orig = item.get("origin_code", origin)
                    dest = item.get("destination_code", destination)
                    detail = item.get("description", "")
                    label = "One-way" if trip_type == "one_way" else "Round-trip"
                    flights.append(
                        FlightOption(
                            origin=orig,
                            destination=dest,
                            departure_date=departure_date,
                            return_date=ret_date,
                            cost_estimate=cost,
                            description=f"{label} · {detail}" if detail else label,
                            airline=item.get("airline"),
                            flight_number=item.get("flight_number"),
                            link=_build_flight_link(orig, dest, departure_date, ret_date)
                        if not _is_valid_link(item.get("link"))
                        else item.get("link").strip(),
                        )
                    )
                except (InvalidOperation, TypeError):
                    continue
            return flights
        except Exception:
            return []

    def get_hotel_options(
        self,
        destination: str,
        check_in_date: date,
        check_out_date: date,
        budget_hint: Optional[Decimal] = None,
    ) -> List[HotelOption]:
        """Search for hotel options (used when fetching hotels separately)."""
        budget = budget_hint or Decimal("500")
        _, hotels = self.get_trip_suggestions(
            "NYC", destination, check_in_date, check_out_date, 1, budget
        )
        return hotels

    def get_activity_suggestions(
        self,
        day_date: date,
        destination: str,
        preferences: str,
        budget_remaining: Optional[Decimal] = None,
    ) -> List[ActivitySuggestion]:
        """Search web for activities based on user query."""
        prompt = f"""Search the web for activities in {destination}.
User is looking for: {preferences}
Date: {day_date.isoformat()}
Budget for the day: ${budget_remaining or 100}

Find 3-5 specific activities (name, optional time, estimated cost). Return ONLY valid JSON array:
[{{"title": "...", "time": "... or null", "cost_estimate": number or null}}]"""

        try:
            content = self._call_with_web_search(prompt)
            if not content:
                return []
            if content.startswith("```"):
                content = re.sub(r"^```\w*\n?", "", content)
                content = re.sub(r"\n?```$", "", content)
            # Model can prepend prose; extract first JSON array block.
            extracted = _extract_json_block(content, "[", "]")
            if extracted:
                content = extracted
            data = json.loads(content)
            return [
                ActivitySuggestion(
                    title=item.get("title", ""),
                    time=item.get("time"),
                    cost_estimate=Decimal(str(item["cost_estimate"])) if item.get("cost_estimate") else None,
                )
                for item in (data if isinstance(data, list) else [])[:5]
            ]
        except Exception:
            return []
