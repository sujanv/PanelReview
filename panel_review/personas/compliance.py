"""
Compliance & Privacy Engineer persona for data governance, licensing, and regulatory safety.
"""

from typing import Optional, List
from panel_review.personas.base import Persona


class ComplianceEngineerPersona(Persona):
    def __init__(
        self,
        name: str = "Compliance & Privacy Engineer",
        title: str = "Data Governance & Policy Specialist",
        emoji: str = "📜",
        focus_areas: Optional[List[str]] = None,
        severity_threshold: str = "MEDIUM",
        custom_system_prompt: Optional[str] = None,
    ):
        defaults = [
            "Personally Identifiable Information (PII) handling (GDPR / CCPA / HIPAA)",
            "Data residency, encryption-at-rest and in-transit requirements",
            "Open source software license compliance (GPL vs MIT/Apache-2.0)",
            "Audit trails and immutability for security-critical actions",
            "Data retention, anonymization, and right-to-be-forgotten deletion workflows",
        ]
        super().__init__(
            persona_id="compliance",
            name=name,
            title=title,
            emoji=emoji,
            focus_areas=focus_areas or defaults,
            severity_threshold=severity_threshold,
            custom_system_prompt=custom_system_prompt,
        )
