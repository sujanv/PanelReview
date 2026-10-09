"""
Software Architect persona for design patterns, modularity, and clean code principles.
"""

from typing import Optional, List
from panel_review.personas.base import Persona


class SoftwareArchitectPersona(Persona):
    def __init__(
        self,
        name: str = "Software Architect",
        title: str = "Clean Architecture & Modularity Specialist",
        emoji: str = "🏗️",
        focus_areas: Optional[List[str]] = None,
        severity_threshold: str = "LOW",
        custom_system_prompt: Optional[str] = None,
    ):
        defaults = [
            "SOLID, DRY, and KISS design principles adherence",
            "Separation of concerns and domain isolation (ports and adapters / hexagonal)",
            "Coupling, cohesion, and dependency inversion (DIP)",
            "API design ergonomics, error hierarchies, and return contract clarity",
            "Cyclomatic complexity and code maintainability",
            "Naming clarity, idiomatic language patterns, and readability",
        ]
        super().__init__(
            persona_id="architecture",
            name=name,
            title=title,
            emoji=emoji,
            focus_areas=focus_areas or defaults,
            severity_threshold=severity_threshold,
            custom_system_prompt=custom_system_prompt,
        )
