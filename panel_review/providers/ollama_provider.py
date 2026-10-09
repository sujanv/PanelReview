"""
Ollama local model provider.
"""

import json
import urllib.request
import urllib.error
from typing import Optional
from panel_review.providers.base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(
        self,
        model: str = "llama3.3",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        timeout_seconds: int = 120,
    ):
        base = base_url or "http://localhost:11434"
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base.rstrip("/"),
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
        )

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        url = f"{self.base_url}/api/chat"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            }
        }

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "PanelReview/1.0",
        }

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
                res_json = json.loads(body)
                return res_json.get("message", {}).get("content", "")
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. Ensure Ollama is running (`ollama serve`). Details: {e}"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Ollama execution error: {e}") from e
