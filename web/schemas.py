"""
Pydantic schemas for API request validation.
"""

from datetime import date
from decimal import Decimal
from typing import Optional, Union

from pydantic import BaseModel, field_validator


def _strip_optional(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


class CreateTripRequest(BaseModel):
    origin: str
    destination: str
    per_person_budget: Union[Decimal, float]
    num_people: int
    start_date: date
    end_date: date
    activity_preferences: str = ""
    name: str = ""

    @field_validator("origin", "destination", mode="before")
    @classmethod
    def strip_string(cls, v):
        return (v or "").strip()

    @field_validator("origin")
    @classmethod
    def origin_not_empty(cls, v):
        if not v:
            raise ValueError("origin is required")
        return v

    @field_validator("destination")
    @classmethod
    def destination_not_empty(cls, v):
        if not v:
            raise ValueError("destination is required")
        return v

    @field_validator("per_person_budget", mode="before")
    @classmethod
    def to_decimal(cls, v):
        if v is None:
            raise ValueError("per_person_budget is required")
        try:
            return Decimal(str(v))
        except Exception:
            raise ValueError("per_person_budget must be a number")

    @field_validator("num_people")
    @classmethod
    def num_people_positive(cls, v):
        if v < 1:
            raise ValueError("num_people must be at least 1")
        return v

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if hasattr(v, "year"):
            return v
        if not v or not str(v).strip():
            raise ValueError("date is required")
        from datetime import datetime
        try:
            return datetime.strptime(str(v).strip()[:10], "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("date must be YYYY-MM-DD")


class UpdateDescriptionRequest(BaseModel):
    description: Optional[str] = None

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, v):
        return _strip_optional(v)


class JoinTripRequest(BaseModel):
    name: str
    budget: Union[Decimal, float]

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v):
        s = (v or "").strip()
        if not s:
            raise ValueError("name is required")
        return s

    @field_validator("budget", mode="before")
    @classmethod
    def to_decimal(cls, v):
        if v is None:
            raise ValueError("budget is required")
        try:
            return Decimal(str(v))
        except Exception:
            raise ValueError("budget must be a number")


class AddFlightRequest(BaseModel):
    origin: str
    destination: str
    departure_date: date
    return_date: date
    cost_estimate: Union[Decimal, float]
    departure_time: Optional[str] = None
    link: Optional[str] = None

    @field_validator("origin", "destination", mode="before")
    @classmethod
    def strip_string(cls, v):
        return (v or "").strip()

    @field_validator("origin")
    @classmethod
    def origin_not_empty(cls, v):
        if not v:
            raise ValueError("origin is required")
        return v

    @field_validator("destination")
    @classmethod
    def destination_not_empty(cls, v):
        if not v:
            raise ValueError("destination is required")
        return v

    @field_validator("departure_date", "return_date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if hasattr(v, "year"):
            return v
        if not v or not str(v).strip():
            raise ValueError("date is required")
        from datetime import datetime
        try:
            return datetime.strptime(str(v).strip()[:10], "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("date must be YYYY-MM-DD")

    @field_validator("cost_estimate", mode="before")
    @classmethod
    def to_decimal(cls, v):
        if v is None:
            raise ValueError("cost_estimate is required")
        try:
            return Decimal(str(v))
        except Exception:
            raise ValueError("cost_estimate must be a number")

    @field_validator("departure_time", "link", mode="before")
    @classmethod
    def strip_optional(cls, v):
        return _strip_optional(v)


class AddHotelRequest(BaseModel):
    name: str
    check_in_date: date
    check_out_date: date
    cost_estimate: Union[Decimal, float]
    link: Optional[str] = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v):
        s = (v or "").strip()
        if not s:
            raise ValueError("name is required")
        return s

    @field_validator("check_in_date", "check_out_date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if hasattr(v, "year"):
            return v
        if not v or not str(v).strip():
            raise ValueError("date is required")
        from datetime import datetime
        try:
            return datetime.strptime(str(v).strip()[:10], "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("date must be YYYY-MM-DD")

    @field_validator("cost_estimate", mode="before")
    @classmethod
    def to_decimal(cls, v):
        if v is None:
            raise ValueError("cost_estimate is required")
        try:
            return Decimal(str(v))
        except Exception:
            raise ValueError("cost_estimate must be a number")

    @field_validator("link", mode="before")
    @classmethod
    def strip_optional(cls, v):
        return _strip_optional(v)


class AddActivityRequest(BaseModel):
    day_id: int
    title: str
    time: Optional[str] = None
    cost_estimate: Optional[Union[Decimal, float]] = None

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v):
        s = (v or "").strip()
        if not s:
            raise ValueError("title is required")
        return s

    @field_validator("cost_estimate", mode="before")
    @classmethod
    def to_decimal(cls, v):
        if v is None:
            return None
        try:
            return Decimal(str(v))
        except Exception:
            raise ValueError("cost_estimate must be a number")

    @field_validator("time", mode="before")
    @classmethod
    def strip_optional(cls, v):
        return _strip_optional(v)


class MoveActivityRequest(BaseModel):
    day_id: int
    order: int = 0


class ReorderActivitiesRequest(BaseModel):
    day_id: int
    activity_ids: list[int]

    @field_validator("activity_ids")
    @classmethod
    def activity_ids_not_empty(cls, v):
        if not v:
            raise ValueError("activity_ids cannot be empty")
        return v
