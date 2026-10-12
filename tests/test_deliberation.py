import unittest
from panel_review.models import PersonaReviewResult, ReviewVerdict
from panel_review.engine.deliberation import DeliberationEngine


class TestDeliberation(unittest.TestCase):
    def test_deliberation_round(self):
        sec = PersonaReviewResult(
            persona_id="security",
            persona_name="Security Engineer",
            persona_title="Sec",
            persona_emoji="🛡️",
            model_used="mock",
            summary="sec ok",
            score=85,
            findings=[],
        )
        perf = PersonaReviewResult(
            persona_id="performance",
            persona_name="Performance Engineer",
            persona_title="Perf",
            persona_emoji="⚡",
            model_used="mock",
            summary="perf ok",
            score=88,
            findings=[],
        )

        transcript = DeliberationEngine.conduct_deliberation([sec, perf])
        self.assertGreater(transcript.rounds_conducted, 0)
        self.assertGreater(len(transcript.debates), 0)
        md = transcript.to_markdown()
        self.assertIn("Panel Cross-Examination", md)


if __name__ == "__main__":
    unittest.main()
