"""
User persistence for authentication.
"""

from typing import Optional

from persistence.sqlite.models import UserModel, db


def get_user_by_email(email: str) -> Optional[UserModel]:
    """Return user by email, or None."""
    return UserModel.query.filter_by(email=email.strip().lower()).first()


def get_user_by_id(user_id: int) -> Optional[UserModel]:
    """Return user by id, or None."""
    return UserModel.query.get(user_id)


def create_user(email: str, password_hash: str, name: Optional[str] = None) -> UserModel:
    """Create and persist a user. Email must be unique."""
    user = UserModel(
        email=email.strip().lower(),
        password_hash=password_hash,
        name=name.strip() if name else None,
    )
    db.session.add(user)
    db.session.commit()
    return user


def update_user_name(user_id: int, name: str) -> bool:
    """Update user's display name. Returns True if updated."""
    user = UserModel.query.get(user_id)
    if not user:
        return False
    user.name = (name or "").strip() or None
    db.session.commit()
    return True
