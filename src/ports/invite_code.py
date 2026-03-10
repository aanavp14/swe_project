"""
Interface for invite code generation.

Abstraction allows tests to inject a predictable generator (e.g. always "TEST123").
Production uses RandomInviteCodeGenerator.
"""

from typing import Protocol


class InviteCodeGenerator(Protocol):
    """Generate unique invite codes for trips."""

    def generate(self) -> str:
        """Return a new invite code."""
        ...
