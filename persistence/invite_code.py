"""
Concrete invite code generator.

Uses random alphanumeric chars. Inject this into CreateTripService.
For tests, inject a fake that returns predictable codes.
"""

import random
import string


class RandomInviteCodeGenerator:
    """Generate random alphanumeric invite codes."""

    LENGTH = 8
    CHARS = string.ascii_uppercase + string.digits

    def generate(self) -> str:
        """Return a new random invite code."""
        return "".join(random.choices(self.CHARS, k=self.LENGTH))
