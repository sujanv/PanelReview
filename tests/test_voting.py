import unittest
from panel_review.models import PersonaReviewResult, ReviewVerdict
from panel_review.engine.consensus_voting import ConsensusVotingEngine, VotingStrategy


class TestVoting(unittest.TestCase):
    def test_weighted_domain_voting(self):
        # Security has low score (60), Architecture has high score (95)
        sec = PersonaReviewResult(
            persona_id="security",
            persona_name="Security",
            persona_title="",
            persona_emoji="",
            model_used="",
            summary="",
            score=60,
            verdict=ReviewVerdict.NEEDS_REVISION,
        )
        arch = PersonaReviewResult(
            persona_id="architecture",
            persona_name="Architecture",
            persona_title="",
            persona_emoji="",
            model_used="",
            summary="",
            score=95,
            verdict=ReviewVerdict.APPROVED,
        )

        score_weighted, _ = ConsensusVotingEngine.calculate_score([sec, arch], VotingStrategy.WEIGHTED_DOMAIN)
        score_avg, _ = ConsensusVotingEngine.calculate_score([sec, arch], VotingStrategy.SIMPLE_AVERAGE)

        # Because security is weighted 1.5x vs architecture 1.0x, weighted score must be lower than simple average
        self.assertLess(score_weighted, score_avg)

    def test_pessimistic_worst_case_voting(self):
        sec = PersonaReviewResult(
            persona_id="security",
            persona_name="Security",
            persona_title="",
            persona_emoji="",
            model_used="",
            summary="",
            score=55,
            verdict=ReviewVerdict.NEEDS_REVISION,
        )
        perf = PersonaReviewResult(
            persona_id="performance",
            persona_name="Performance",
            persona_title="",
            persona_emoji="",
            model_used="",
            summary="",
            score=90,
            verdict=ReviewVerdict.APPROVED,
        )
        score_min, _ = ConsensusVotingEngine.calculate_score([sec, perf], VotingStrategy.PESSIMISTIC_WORST_CASE)
        self.assertEqual(score_min, 55)


if __name__ == "__main__":
    unittest.main()
