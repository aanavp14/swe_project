"""AI suggestion implementations (mock, OpenAI, etc.)."""

from persistence.ai.mock_suggestions import MockAISuggestionsService
from persistence.ai.openai_suggestions import OpenAISuggestionsService

__all__ = ["MockAISuggestionsService", "OpenAISuggestionsService"]
