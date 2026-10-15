import unittest
from panel_review.models import ConsensusReport, ReviewFinding, SeverityLevel, ReviewVerdict, RepositoryInfo, PersonaReviewResult
from panel_review.ci.pr_bot import PRCommentGenerator


class TestPRBot(unittest.TestCase):
    def test_format_pr_comment(self):
        repo = RepositoryInfo(source="test_repo", is_remote=False)
        finding = ReviewFinding(
            title="Insecure Storage",
            severity=SeverityLevel.HIGH,
            file_path="storage.py",
            line_number=10,
            description="Cleartext sensitive data",
            recommendation="Encrypt at rest",
            category="Security",
            persona_id="security",
        )
        persona_res = PersonaReviewResult(
            persona_id="security",
            persona_name="Security Engineer",
            persona_title="AppSec",
            persona_emoji="🛡️",
            model_used="gpt-4o",
            summary="Identified cleartext storage risk.",
            score=70,
            findings=[finding],
            verdict=ReviewVerdict.NEEDS_REVISION,
        )
        report = ConsensusReport(
            timestamp="2026-10-14T00:00:00Z",
            repository=repo,
            overall_verdict=ReviewVerdict.NEEDS_REVISION,
            overall_score=70,
            persona_results=[persona_res],
            consolidated_findings=[finding],
            executive_summary="Code requires remediation before merge.",
            action_items=["Encrypt data at rest in storage.py"],
        )

        comment = PRCommentGenerator.format_pr_comment(report)
        self.assertIn("AI Panel Review Summary", comment)
        self.assertIn("<details><summary>", comment)
        self.assertIn("- [ ] Encrypt data at rest in storage.py", comment)
        self.assertIn("NEEDS_REVISION", comment)


if __name__ == "__main__":
    unittest.main()
