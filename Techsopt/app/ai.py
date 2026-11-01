from abc import ABC, abstractmethod
from .config import settings

class AIService(ABC):
    @abstractmethod
    def complete(self, prompt: str, context: dict) -> str: ...

class DisabledAIService(AIService):
    def complete(self, prompt: str, context: dict) -> str:
        raise RuntimeError('AI provider is not configured')

def get_ai_service() -> AIService:
    # Provider adapters can be added without changing routers/business rules.
    return DisabledAIService()
