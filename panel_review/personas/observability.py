"""
Observability & SRE Engineer persona for telemetry, resilience, and operational health.
"""

from typing import Optional, List
from panel_review.personas.base import Persona


class ObservabilityEngineerPersona(Persona):
    def __init__(
        self,
        name: str = "Observability & SRE Engineer",
        title: str = "Telemetry, Resilience & Production Readiness Specialist",
        emoji: str = "📡",
        focus_areas: Optional[List[str]] = None,
        severity_threshold: str = "MEDIUM",
        custom_system_prompt: Optional[str] = None,
    ):
        defaults = [
            "Structured logging with correlation IDs and standard log levels",
            "Distributed tracing context propagation (OpenTelemetry standards)",
            "Operational telemetry: latency, throughput, error rate metrics",
            "Explicit I/O network timeouts, retries with backoff/jitter",
            "Circuit breakers and failure blast-radius isolation",
            "Health checks, readiness and liveness endpoints",
            "PII and secret masking before log emission",
        ]
        super().__init__(
            persona_id="observability",
            name=name,
            title=title,
            emoji=emoji,
            focus_areas=focus_areas or defaults,
            severity_threshold=severity_threshold,
            custom_system_prompt=custom_system_prompt,
        )
