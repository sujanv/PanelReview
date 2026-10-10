"""
Security Engineer persona for application security, threat modeling, and OWASP review.
"""

from typing import Optional, List
from panel_review.personas.base import Persona


class SecurityEngineerPersona(Persona):
    def __init__(
        self,
        name: str = "Security Engineer",
        title: str = "Application Security & Threat Modeling Specialist",
        emoji: str = "🛡️",
        focus_areas: Optional[List[str]] = None,
        severity_threshold: str = "LOW",
        custom_system_prompt: Optional[str] = None,
    ):
        defaults = [
            "OWASP Top 10 vulnerabilities (SQLi, XSS, SSRF, Broken Auth)",
            "Hardcoded secrets, API tokens, cryptographic private keys",
            "Command injection, unsafe subprocesses, and dynamic evaluation",
            "Cryptographic algorithm security and secure random generation",
            "Insecure deserialization and XML entity parsing",
            "Authentication, session management, and authorization checks",
        ]
        super().__init__(
            persona_id="security",
            name=name,
            title=title,
            emoji=emoji,
            focus_areas=focus_areas or defaults,
            severity_threshold=severity_threshold,
            custom_system_prompt=custom_system_prompt,
        )
