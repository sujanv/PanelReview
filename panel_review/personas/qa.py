"""
QA & Reliability Engineer persona for testability, boundary coverage, and defensive coding.
"""

from typing import Optional, List
from panel_review.personas.base import Persona


class QAEngineerPersona(Persona):
    def __init__(
        self,
        name: str = "QA & Reliability Engineer",
        title: str = "Test Engineering & Edge Case Specialist",
        emoji: str = "🧪",
        focus_areas: Optional[List[str]] = None,
        severity_threshold: str = "LOW",
        custom_system_prompt: Optional[str] = None,
    ):
        defaults = [
            "Testability and dependency injection for easy mocking",
            "Edge cases: empty inputs, zero division, overflow, Unicode strings",
            "Defensive programming: null/nil pointer dereference hazards",
            "Error propagation completeness and absence of silent unhandled states",
            "Deterministic test behavior and absence of race conditions",
            "Integration test boundaries and contract assertions",
        ]
        super().__init__(
            persona_id="qa",
            name=name,
            title=title,
            emoji=emoji,
            focus_areas=focus_areas or defaults,
            severity_threshold=severity_threshold,
            custom_system_prompt=custom_system_prompt,
        )
