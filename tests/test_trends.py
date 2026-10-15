import os
import unittest
import tempfile
from panel_review.models import ConsensusReport, ReviewFinding, SeverityLevel, ReviewVerdict, RepositoryInfo
from panel_review.engine.trends import TrendTracker


class TestTrends(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name

    def tearDown(self):
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)

    def test_record_trend_and_regression(self):
        repo = RepositoryInfo(source="test_repo", is_remote=False, branch="main", commit_hash="c111")
        report1 = ConsensusReport(
            timestamp="2026-10-14T00:00:00Z",
            repository=repo,
            overall_verdict=ReviewVerdict.APPROVED,
            overall_score=90,
            consolidated_findings=[],
        )
        res1 = TrendTracker.record_run(report1, history_file=self.temp_file)
        self.assertEqual(res1["total_runs_recorded"], 1)

        # Run 2: regression
        crit_finding = ReviewFinding(
            title="Exposed Secret",
            severity=SeverityLevel.CRITICAL,
            file_path="app.py",
            line_number=1,
            description="Leaked token",
            recommendation="Revoke",
        )
        report2 = ConsensusReport(
            timestamp="2026-10-14T01:00:00Z",
            repository=repo,
            overall_verdict=ReviewVerdict.REJECTED,
            overall_score=70,
            consolidated_findings=[crit_finding],
        )
        res2 = TrendTracker.record_run(report2, history_file=self.temp_file)
        self.assertEqual(res2["total_runs_recorded"], 2)
        comp = res2["comparison"]
        self.assertTrue(comp["is_regression"])
        self.assertEqual(comp["score_delta"], -20)
        self.assertEqual(comp["critical_delta"], 1)

        summary = TrendTracker.format_trend_summary(res2)
        self.assertIn("REGRESSION WARNING", summary)


if __name__ == "__main__":
    unittest.main()
