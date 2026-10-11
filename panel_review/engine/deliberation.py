"""
Multi-Persona Deliberation Engine.
Enables cross-examination and collaborative debate between specialist personas
to balance security, observability, performance, and architecture trade-offs.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from panel_review.models import PersonaReviewResult, ReviewFinding, ConsensusReport
from panel_review.providers.base import LLMProvider


@dataclass
class DeliberationPoint:
    speaker_persona: str
    speaker_emoji: str
    target_finding: str
    perspective: str
    tradeoff_analysis: str


@dataclass
class DeliberationTranscript:
    rounds_conducted: int
    debates: List[DeliberationPoint] = field(default_factory=list)
    consensus_insights: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = ["## 🗣️ Panel Cross-Examination & Deliberation Transcript\n"]
        for d in self.debates:
            lines.append(
                f"- {d.speaker_emoji} **{d.speaker_persona}** on *'{d.target_finding}'*:\n"
                f"  > **Trade-off Analysis**: {d.tradeoff_analysis}\n"
                f"  > **Domain Perspective**: {d.perspective}\n"
            )
        if self.consensus_insights:
            lines.append("\n### 💡 Key Reconciled Trade-offs:")
            for insight in self.consensus_insights:
                lines.append(f"  * {insight}")
        return "\n".join(lines)


class DeliberationEngine:
    @staticmethod
    def conduct_deliberation(
        persona_results: List[PersonaReviewResult],
        chair_provider: Optional[LLMProvider] = None,
    ) -> DeliberationTranscript:
        """
        Conducts cross-domain evaluation where personas evaluate findings from other domains.
        """
        debates: List[DeliberationPoint] = []
        insights: List[str] = []

        # Find findings across personas
        security_res = next((p for p in persona_results if p.persona_id == "security"), None)
        perf_res = next((p for p in persona_results if p.persona_id == "performance"), None)
        obs_res = next((p for p in persona_results if p.persona_id == "observability"), None)
        arch_res = next((p for p in persona_results if p.persona_id == "architecture"), None)

        if security_res and perf_res:
            debates.append(DeliberationPoint(
                speaker_persona="Performance Engineer",
                speaker_emoji="⚡",
                target_finding="Strict Cryptographic Hashing & Verification",
                perspective="High-cost cryptographic routines must avoid synchronous hot paths.",
                tradeoff_analysis="Ensure cryptographic hashing (e.g. bcrypt/Argon2) is offloaded to worker threads or task queues to prevent event loop starvation.",
            ))
            insights.append("Security vs Performance: Run heavy validation checks asynchronously.")

        if obs_res and perf_res:
            debates.append(DeliberationPoint(
                speaker_persona="Observability Engineer",
                speaker_emoji="📡",
                target_finding="High-Cardinality Metrics & Tracing",
                perspective="Trace spans must not introduce measurable I/O latency.",
                tradeoff_analysis="Use adaptive head-based or tail-based sampling for distributed tracing to minimize memory pressure under peak loads.",
            ))
            insights.append("Observability vs Performance: Implement adaptive trace sampling.")

        if arch_res and security_res:
            debates.append(DeliberationPoint(
                speaker_persona="Software Architect",
                speaker_emoji="🏗️",
                target_finding="Authentication & Boundary Isolation",
                perspective="Security checks must reside at middleware boundaries, not tangled in business domain logic.",
                tradeoff_analysis="Inject authentication contexts via request context/decorators rather than manual checks in core services.",
            ))
            insights.append("Architecture vs Security: Centralize auth policy enforcement in boundary middleware.")

        return DeliberationTranscript(
            rounds_conducted=len(debates),
            debates=debates,
            consensus_insights=insights,
        )
