"""
Google Gemini provider.
"""

import json
import urllib.request
import urllib.error
from typing import Optional
from panel_review.providers.base import LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(
        self,
        model: str = "gemini-1.5-pro",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        timeout_seconds: int = 60,
    ):
        base = base_url or "https://generativelanguage.googleapis.com/v1beta"
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
            raise ValueError("Gemini API key is missing. Set GEMINI_API_KEY environment variable.")

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        contents = []
        if system_prompt:
            # Add system instruction if supported or prepend to conversation
            contents.append({
                "role": "user",
                "parts": [{"text": f"[SYSTEM INSTRUCTION]: {system_prompt}\n\n[USER REQUEST]: {prompt}"}]
            })
        else:
            contents.append({
                "role": "user",
                "parts": [{"text": prompt}]
            })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
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
                candidates = res_json.get("candidates", [])
                if not candidates:
                    return ""
                parts = candidates[0].get("content", {}).get("parts", [])
                return "".join([p.get("text", "") for p in parts])
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"Gemini API error {e.code}: {e.reason} - {err_body}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to communicate with Gemini endpoint: {e}") from e
