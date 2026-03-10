"""Repository for cached AI suggestions (voting)."""
from typing import List, Optional, Tuple

from persistence.sqlite.models import SuggestionModel, SuggestionVoteModel, db


def delete_by_trip_id(trip_id: int) -> None:
    """Remove all suggestions for a trip (before fetching new ones)."""
    SuggestionModel.query.filter_by(trip_id=trip_id).delete()
    db.session.commit()


def create_many(trip_id: int, suggestion_type: str, items: List[dict]) -> List[SuggestionModel]:
    """Store suggestions. Each item is a dict (flight or hotel data)."""
    import json
    models = []
    for item in items:
        m = SuggestionModel(
            trip_id=trip_id,
            suggestion_type=suggestion_type,
            data=json.dumps(item, default=str),
            vote_count=0,
        )
        db.session.add(m)
        models.append(m)
    db.session.commit()
    return models


def get_by_trip_id(trip_id: int) -> List[SuggestionModel]:
    """Get all suggestions for a trip, ordered by vote_count desc then id."""
    return (
        SuggestionModel.query.filter_by(trip_id=trip_id)
        .order_by(SuggestionModel.vote_count.desc(), SuggestionModel.id.asc())
        .all()
    )


def get_by_id(suggestion_id: int) -> Optional[SuggestionModel]:
    """Get suggestion by id."""
    return SuggestionModel.query.get(suggestion_id)


def get_voted_suggestion_ids(user_id: int, suggestion_ids: List[int]) -> set:
    """Return set of suggestion_ids the user has voted on."""
    if not suggestion_ids:
        return set()
    rows = (
        SuggestionVoteModel.query.filter(
            SuggestionVoteModel.suggestion_id.in_(suggestion_ids),
            SuggestionVoteModel.user_id == user_id,
        )
        .with_entities(SuggestionVoteModel.suggestion_id)
        .all()
    )
    return {r[0] for r in rows}


def has_user_voted(suggestion_id: int, user_id: int) -> bool:
    """Check if user has already voted on this suggestion."""
    return (
        SuggestionVoteModel.query.filter_by(
            suggestion_id=suggestion_id, user_id=user_id
        ).first()
        is not None
    )


def increment_vote(suggestion_id: int, user_id: int) -> Tuple[Optional[int], bool]:
    """
    Add vote if user hasn't voted. Returns (vote_count, did_vote).
    did_vote is False if user already voted.
    """
    m = SuggestionModel.query.get(suggestion_id)
    if not m:
        return None, False
    if has_user_voted(suggestion_id, user_id):
        return m.vote_count, False
    vote = SuggestionVoteModel(suggestion_id=suggestion_id, user_id=user_id)
    db.session.add(vote)
    m.vote_count = (m.vote_count or 0) + 1
    db.session.commit()
    db.session.refresh(m)
    return m.vote_count, True
