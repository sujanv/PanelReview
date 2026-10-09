"""
Anthropic Claude provider.
"""

import json
import urllib.request
import urllib.error
from typing import Optional
from panel_review.providers.base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        timeout_seconds: int = 60,
    ):
        base = base_url or "https://api.anthropic.com/v1"
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base.rstrip("/"),
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
        )

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            raise ValueError("Anthropic API key is missing. Set ANTHROPIC_API_KEY environment variable.")

        url = f"{self.base_url}/messages"
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }
        if system_prompt:
            payload["system"] = system_prompt

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "User-Agent": "PanelReview/1.0",
        }

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
                res_json = json.loads(body)
                content_blocks = res_json.get("content", [])
                text_parts = [c.get("text", "") for c in content_blocks if c.get("type") == "text"]
                return "".join(text_parts)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"Anthropic API error {e.code}: {e.reason} - {err_body}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to communicate with Anthropic endpoint: {e}") from e
