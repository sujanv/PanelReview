"""
Consensus Voting Strategies for AI Panel Reviews.
Implements alternative consensus aggregation algorithms: Weighted Domain, Borda Count, and Pessimistic Worst-Case.
"""

from enum import Enum
from typing import List, Dict, Tuple
from panel_review.models import PersonaReviewResult, ReviewVerdict


class VotingStrategy(str, Enum):
    SIMPLE_AVERAGE = "simple_average"
    WEIGHTED_DOMAIN = "weighted_domain"
    BORDA_COUNT = "borda_count"
    PESSIMISTIC_WORST_CASE = "pessimistic_worst_case"


# Domain weighting multipliers (e.g., Security & SRE have critical weight on deployability)
DOMAIN_WEIGHTS: Dict[str, float] = {
    "security": 1.5,
    "observability": 1.3,
    "performance": 1.2,
    "architecture": 1.0,
    "qa": 1.1,
    "compliance": 1.2,
}


class ConsensusVotingEngine:
    @staticmethod
    def calculate_score(
        persona_results: List[PersonaReviewResult],
        strategy: VotingStrategy = VotingStrategy.WEIGHTED_DOMAIN,
    ) -> Tuple[int, ReviewVerdict]:
        """
        Calculates calibrated score and verdict using the chosen voting strategy.
        """
        if not persona_results:
            return 100, ReviewVerdict.APPROVED

        if strategy == VotingStrategy.SIMPLE_AVERAGE:
            avg_score = int(sum(p.score for p in persona_results) / len(persona_results))
            return avg_score, ConsensusVotingEngine._score_to_verdict(avg_score, persona_results)

        elif strategy == VotingStrategy.PESSIMISTIC_WORST_CASE:
            # Score is bounded by the lowest individual domain score
            min_score = min(p.score for p in persona_results)
            return min_score, ConsensusVotingEngine._score_to_verdict(min_score, persona_results)

        elif strategy == VotingStrategy.BORDA_COUNT:
            # Ranked preference aggregation
            sorted_by_score = sorted(persona_results, key=lambda x: x.score)
            borda_points = sum(idx * p.score for idx, p in enumerate(sorted_by_score, 1))
            max_points = sum(idx * 100 for idx in range(1, len(persona_results) + 1))
            calibrated = int((borda_points / max_points) * 100) if max_points > 0 else 100
            return calibrated, ConsensusVotingEngine._score_to_verdict(calibrated, persona_results)

        else:  # WEIGHTED_DOMAIN (default)
            total_weighted_score = 0.0
            total_weight = 0.0

            for p in persona_results:
                weight = DOMAIN_WEIGHTS.get(p.persona_id, 1.0)
                total_weighted_score += p.score * weight
                total_weight += weight

            calibrated = int(total_weighted_score / total_weight) if total_weight > 0 else 100
            return calibrated, ConsensusVotingEngine._score_to_verdict(calibrated, persona_results)

    @staticmethod
    def _score_to_verdict(score: int, persona_results: List[PersonaReviewResult]) -> ReviewVerdict:
        # Check if any persona has critical blocker
        for p in persona_results:
            if p.verdict == ReviewVerdict.REJECTED:
                return ReviewVerdict.REJECTED

        if score >= 90:
            return ReviewVerdict.APPROVED
        elif score >= 75:
            return ReviewVerdict.APPROVED_WITH_CONDITIONS
        elif score >= 50:
            return ReviewVerdict.NEEDS_REVISION
        else:
            return ReviewVerdict.REJECTED
