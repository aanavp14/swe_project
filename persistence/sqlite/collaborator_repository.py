"""
SQLite implementation of CollaboratorRepository.

Converts between domain Collaborator and CollaboratorModel.
"""

from decimal import Decimal
from typing import Optional

from src.domain.trip import Collaborator

from persistence.sqlite.models import CollaboratorModel, db


class SqliteCollaboratorRepository:
    """CollaboratorRepository implementation using SQLite."""

    def create(self, collaborator: Collaborator, user_id: Optional[int] = None) -> Collaborator:
        """Save collaborator to DB and return it with id set. Optionally link to user for leave trip."""
        model = CollaboratorModel(
            trip_id=collaborator.trip_id,
            name=collaborator.name,
            budget=collaborator.budget,
            user_id=user_id,
        )
        db.session.add(model)
        db.session.commit()
        return Collaborator(
            id=model.id,
            trip_id=model.trip_id,
            name=model.name,
            budget=Decimal(str(model.budget)),  # Ensure Decimal for domain
        )

    def get_by_trip_id_and_user_id(self, trip_id: int, user_id: int) -> Optional[Collaborator]:
        """Load collaborator for trip and user, or None."""
        model = CollaboratorModel.query.filter_by(trip_id=trip_id, user_id=user_id).first()
        if model is None:
            return None
        return Collaborator(
            id=model.id,
            trip_id=model.trip_id,
            name=model.name,
            budget=Decimal(str(model.budget)),
        )

    def get_by_trip_id(self, trip_id: int) -> list[Collaborator]:
        """Load all collaborators for a trip."""
        models = CollaboratorModel.query.filter_by(trip_id=trip_id).all()
        return [
            Collaborator(
                id=m.id,
                trip_id=m.trip_id,
                name=m.name,
                budget=Decimal(str(m.budget)),
            )
            for m in models
        ]

    def delete_by_id(self, collaborator_id: int) -> bool:
        """Delete one collaborator by id."""
        model = CollaboratorModel.query.get(collaborator_id)
        if model is None:
            return False
        db.session.delete(model)
        db.session.commit()
        return True
