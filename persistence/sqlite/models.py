"""
SQLAlchemy models for persistence.

These map to DB tables (trips, days, collaborators, flights, hotels). Repositories
convert between these and domain dataclasses. All DB/ORM logic lives here.
"""
from __future__ import annotations

from datetime import date as date_type, datetime as datetime_type
from decimal import Decimal
from typing import Optional

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship

db = SQLAlchemy()  # Initialized with app in app.py


class UserModel(UserMixin, db.Model):
    """User account for authentication."""

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    dietary_prefs: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    loyalty_programs: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)


class TripModel(db.Model):
    """Trip table."""

    __tablename__ = "trips"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    origin: Mapped[str] = mapped_column(db.String(255), nullable=False)
    destination: Mapped[str] = mapped_column(db.String(255), nullable=False)
    per_person_budget: Mapped[Decimal] = mapped_column(db.Numeric(12, 2), nullable=False)
    num_people: Mapped[int] = mapped_column(db.Integer, nullable=False)
    start_date: Mapped[date_type] = mapped_column(db.Date, nullable=False)
    end_date: Mapped[date_type] = mapped_column(db.Date, nullable=False)
    activity_preferences: Mapped[str] = mapped_column(db.Text, nullable=False)
    invite_code: Mapped[str] = mapped_column(db.String(16), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    owner_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    days: Mapped[list["DayModel"]] = relationship("DayModel", back_populates="trip")
    collaborators: Mapped[list["CollaboratorModel"]] = relationship(
        "CollaboratorModel", back_populates="trip"
    )
    flights: Mapped[list["FlightModel"]] = relationship(
        "FlightModel", back_populates="trip"
    )
    hotels: Mapped[list["HotelModel"]] = relationship(
        "HotelModel", back_populates="trip"
    )


class DayModel(db.Model):
    """Day table."""

    __tablename__ = "days"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("trips.id"), nullable=False)
    date: Mapped[date_type] = mapped_column(db.Date, nullable=False)
    order: Mapped[int] = mapped_column(db.Integer, nullable=False)
    trip: Mapped["TripModel"] = relationship("TripModel", back_populates="days")
    activities: Mapped[list["ActivityModel"]] = relationship(
        "ActivityModel", back_populates="day", order_by="ActivityModel.order"
    )


class ActivityModel(db.Model):
    """Activity table: one activity in a day."""

    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    day_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("days.id"), nullable=False)
    title: Mapped[str] = mapped_column(db.String(255), nullable=False)
    time: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    cost_estimate: Mapped[Optional[Decimal]] = mapped_column(db.Numeric(12, 2), nullable=True)
    order: Mapped[int] = mapped_column(db.Integer, nullable=False)
    day: Mapped["DayModel"] = relationship("DayModel", back_populates="activities")


class CollaboratorModel(db.Model):
    """Collaborator table: one person on a trip with name and budget."""

    __tablename__ = "collaborators"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("trips.id"), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    budget: Mapped[Decimal] = mapped_column(db.Numeric(12, 2), nullable=False)
    trip: Mapped["TripModel"] = relationship("TripModel", back_populates="collaborators")


class FlightModel(db.Model):
    """Flight table: origin → destination and return."""

    __tablename__ = "flights"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("trips.id"), nullable=False)
    origin: Mapped[str] = mapped_column(db.String(255), nullable=False)
    destination: Mapped[str] = mapped_column(db.String(255), nullable=False)
    departure_date: Mapped[date_type] = mapped_column(db.Date, nullable=False)
    return_date: Mapped[date_type] = mapped_column(db.Date, nullable=False)
    cost_estimate: Mapped[Decimal] = mapped_column(db.Numeric(12, 2), nullable=False)
    departure_time: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    link: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    trip: Mapped["TripModel"] = relationship("TripModel", back_populates="flights")


class HotelModel(db.Model):
    """Hotel table: stay with check-in/check-out."""

    __tablename__ = "hotels"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("trips.id"), nullable=False)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    check_in_date: Mapped[date_type] = mapped_column(db.Date, nullable=False)
    check_out_date: Mapped[date_type] = mapped_column(db.Date, nullable=False)
    cost_estimate: Mapped[Decimal] = mapped_column(db.Numeric(12, 2), nullable=False)
    link: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    trip: Mapped["TripModel"] = relationship("TripModel", back_populates="hotels")


class SuggestionModel(db.Model):
    """Cached AI suggestion (flight or hotel) for voting. Replaced when 'Get new options' is clicked."""

    __tablename__ = "suggestions"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("trips.id"), nullable=False)
    suggestion_type: Mapped[str] = mapped_column(db.String(20), nullable=False)  # 'flight' or 'hotel'
    data: Mapped[str] = mapped_column(db.Text, nullable=False)  # JSON
    vote_count: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)
    created_at: Mapped[datetime_type] = mapped_column(db.DateTime, nullable=False, default=datetime_type.utcnow)


class SuggestionVoteModel(db.Model):
    """One vote per user per suggestion."""

    __tablename__ = "suggestion_votes"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    suggestion_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("suggestions.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    __table_args__ = (db.UniqueConstraint("suggestion_id", "user_id", name="uq_suggestion_user"),)
