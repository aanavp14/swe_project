"""
SQLite implementation of TripRepository and DayRepository.

Converts between domain objects (Trip, Day) and SQLAlchemy models (TripModel, DayModel).
All DB access is in this module.
"""

from decimal import Decimal
from typing import List, Optional

from src.domain.trip import Day, Trip

from persistence.sqlite.models import (
    ActivityModel,
    CollaboratorModel,
    DayModel,
    FlightModel,
    HotelModel,
    SuggestionModel,
    SuggestionVoteModel,
    TripModel,
    db,
)


class SqliteTripRepository:
    """TripRepository implementation using SQLite."""

    def create(self, trip: Trip, owner_id: Optional[int] = None) -> Trip:
        """Save trip to DB and return it with id set. Optionally set owner_id for auth."""
        model = TripModel(
            name=trip.name,
            origin=trip.origin,
            destination=trip.destination,
            per_person_budget=trip.per_person_budget,
            num_people=trip.num_people,
            start_date=trip.start_date,
            end_date=trip.end_date,
            activity_preferences=trip.activity_preferences,
            invite_code=trip.invite_code,
            description=trip.description,
            owner_id=owner_id,
        )
        db.session.add(model)
        db.session.commit()
        return Trip(
            id=model.id,
            name=model.name,
            origin=model.origin,
            destination=model.destination,
            per_person_budget=Decimal(str(model.per_person_budget)),
            num_people=model.num_people,
            start_date=model.start_date,
            end_date=model.end_date,
            activity_preferences=model.activity_preferences or "",
            invite_code=model.invite_code,
            description=getattr(model, "description", None),
        )

    def get_by_invite_code(self, code: str) -> Optional[Trip]:
        """Load trip by invite code, or None if not found."""
        model = TripModel.query.filter_by(invite_code=code).first()
        if model is None:
            return None
        return Trip(
            id=model.id,
            name=model.name,
            origin=model.origin,
            destination=model.destination,
            per_person_budget=Decimal(str(model.per_person_budget)),
            num_people=model.num_people,
            start_date=model.start_date,
            end_date=model.end_date,
            activity_preferences=model.activity_preferences or "",
            invite_code=model.invite_code,
            description=getattr(model, "description", None),
        )

    def update_description(self, invite_code: str, description: Optional[str]) -> Optional[Trip]:
        """Update trip description by invite code. Returns updated trip or None."""
        model = TripModel.query.filter_by(invite_code=invite_code).first()
        if model is None:
            return None
        model.description = description
        db.session.commit()
        return self.get_by_invite_code(invite_code)

    def delete_by_invite_code(self, code: str) -> bool:
        """Delete trip and all related data. Returns True if deleted."""
        model = TripModel.query.filter_by(invite_code=code).first()
        if model is None:
            return False
        trip_id = model.id
        # Delete in order respecting foreign keys
        sug_ids = [r[0] for r in SuggestionModel.query.filter_by(trip_id=trip_id).with_entities(SuggestionModel.id).all()]
        if sug_ids:
            SuggestionVoteModel.query.filter(SuggestionVoteModel.suggestion_id.in_(sug_ids)).delete(synchronize_session=False)
        SuggestionModel.query.filter_by(trip_id=trip_id).delete()
        day_ids = [r[0] for r in DayModel.query.filter_by(trip_id=trip_id).with_entities(DayModel.id).all()]
        if day_ids:
            ActivityModel.query.filter(ActivityModel.day_id.in_(day_ids)).delete(synchronize_session=False)
        DayModel.query.filter_by(trip_id=trip_id).delete()
        CollaboratorModel.query.filter_by(trip_id=trip_id).delete()
        FlightModel.query.filter_by(trip_id=trip_id).delete()
        HotelModel.query.filter_by(trip_id=trip_id).delete()
        db.session.delete(model)
        db.session.commit()
        return True

    def get_by_owner_id(self, owner_id: int) -> List[Trip]:
        """Return all trips owned by the given user."""
        models = TripModel.query.filter_by(owner_id=owner_id).order_by(TripModel.id.desc()).all()
        return [
            Trip(
                id=m.id,
                name=m.name,
                origin=m.origin,
                destination=m.destination,
                per_person_budget=Decimal(str(m.per_person_budget)),
                num_people=m.num_people,
                start_date=m.start_date,
                end_date=m.end_date,
                activity_preferences=m.activity_preferences or "",
                invite_code=m.invite_code,
                description=getattr(m, "description", None),
            )
            for m in models
        ]

    def get_by_collaborator_user_id(self, user_id: int) -> List[Trip]:
        """Return all trips the user has joined (as collaborator)."""
        from persistence.sqlite.models import CollaboratorModel

        trip_ids = [
            r[0]
            for r in CollaboratorModel.query.filter_by(user_id=user_id)
            .with_entities(CollaboratorModel.trip_id)
            .distinct()
            .all()
        ]
        if not trip_ids:
            return []
        models = TripModel.query.filter(TripModel.id.in_(trip_ids)).order_by(
            TripModel.id.desc()
        ).all()
        return [
            Trip(
                id=m.id,
                name=m.name,
                origin=m.origin,
                destination=m.destination,
                per_person_budget=Decimal(str(m.per_person_budget)),
                num_people=m.num_people,
                start_date=m.start_date,
                end_date=m.end_date,
                activity_preferences=m.activity_preferences or "",
                invite_code=m.invite_code,
                description=getattr(m, "description", None),
            )
            for m in models
        ]


class SqliteDayRepository:
    """DayRepository implementation using SQLite."""

    def create(self, day: Day) -> Day:
        """Save day to DB and return it with id set."""
        model = DayModel(
            trip_id=day.trip_id,
            date=day.date,
            order=day.order,
        )
        db.session.add(model)
        db.session.commit()
        return Day(
            id=model.id,
            trip_id=model.trip_id,
            date=model.date,
            order=model.order,
        )

    def get_by_trip_id(self, trip_id: int) -> list[Day]:
        """Load all days for a trip, ordered by order."""
        models = DayModel.query.filter_by(trip_id=trip_id).order_by(DayModel.order).all()
        return [
            Day(
                id=m.id,
                trip_id=m.trip_id,
                date=m.date,
                order=m.order,
            )
            for m in models
        ]
