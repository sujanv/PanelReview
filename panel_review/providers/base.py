"""
Base abstract class for LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class LLMProvider(ABC):
    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        timeout_seconds: int = 60,
    ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Sends a prompt to the model and returns the text response.
        """
        pass

    def test_connection(self) -> Dict[str, Any]:
        """
        Tests whether the model endpoint is reachable and responsive.
        """
        try:
            resp = self.generate(
                prompt="Respond with 'OK' and nothing else.",
                system_prompt="You are a health check assistant.",
            )
            return {"status": "success", "message": "Connection verified", "sample": resp[:50]}
        except Exception as e:
            return {"status": "error", "message": str(e)}
