"""
SQLite implementation of ActivityRepository.
"""

from decimal import Decimal
from typing import Optional

from src.domain.trip import Activity

from persistence.sqlite.models import ActivityModel, DayModel, db


class SqliteActivityRepository:
    """ActivityRepository implementation using SQLite."""

    def create(self, activity: Activity) -> Activity:
        """Save activity to DB and return it with id set."""
        model = ActivityModel(
            day_id=activity.day_id,
            title=activity.title,
            time=activity.time,
            cost_estimate=activity.cost_estimate,
            order=activity.order,
        )
        db.session.add(model)
        db.session.commit()
        return self._to_domain(model)

    def get_by_id(self, activity_id: int) -> Optional[Activity]:
        """Load activity by id, or None."""
        model = ActivityModel.query.get(activity_id)
        if model is None:
            return None
        return self._to_domain(model)

    def get_by_day_id(self, day_id: int) -> list[Activity]:
        """Load all activities for a day, ordered by order."""
        models = ActivityModel.query.filter_by(day_id=day_id).order_by(ActivityModel.order).all()
        return [self._to_domain(m) for m in models]

    def get_by_trip_id(self, trip_id: int) -> list[Activity]:
        """Load all activities for a trip, ordered by day order then activity order."""
        models = (
            ActivityModel.query.join(DayModel)
            .filter(DayModel.trip_id == trip_id)
            .order_by(DayModel.order, ActivityModel.order)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def delete_by_id(self, activity_id: int) -> bool:
        """Delete one activity by id."""
        model = ActivityModel.query.get(activity_id)
        if model is None:
            return False
        db.session.delete(model)
        db.session.commit()
        return True

    def update_order(self, activity_id: int, order: int) -> bool:
        """Update an activity's order."""
        model = ActivityModel.query.get(activity_id)
        if model is None:
            return False
        model.order = order
        db.session.commit()
        return True

    def update_day_and_order(self, activity_id: int, day_id: int, order: int) -> bool:
        """Move activity to a different day and set its order. Shifts existing activities as needed."""
        model = ActivityModel.query.get(activity_id)
        if model is None:
            return False
        # Shift activities in target day that have order >= new order (except the one we're moving)
        for m in ActivityModel.query.filter(
            ActivityModel.day_id == day_id,
            ActivityModel.order >= order,
            ActivityModel.id != activity_id,
        ).all():
            m.order += 1
        model.day_id = day_id
        model.order = order
        db.session.commit()
        return True

    def _to_domain(self, m: ActivityModel) -> Activity:
        cost = None
        if m.cost_estimate is not None:
            cost = Decimal(str(m.cost_estimate))
        return Activity(
            id=m.id,
            day_id=m.day_id,
            title=m.title,
            time=m.time,
            cost_estimate=cost,
            order=m.order,
        )
