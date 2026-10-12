import unittest
import json
from panel_review.models import ConsensusReport, ReviewFinding, SeverityLevel, ReviewVerdict, RepositoryInfo
from panel_review.engine.sarif import SarifExporter


class TestSarif(unittest.TestCase):
    def test_sarif_export_structure(self):
        repo = RepositoryInfo(source="test_repo", is_remote=False)
        finding = ReviewFinding(
            title="SQL Injection Risk",
            severity=SeverityLevel.HIGH,
            file_path="app.py",
            line_number=15,
            description="Direct string formatting in SQL query",
            recommendation="Use parameterized query",
            category="OWASP-A03",
            persona_id="security",
        )
        report = ConsensusReport(
            timestamp="2026-10-09T00:00:00Z",
            repository=repo,
            overall_verdict=ReviewVerdict.NEEDS_REVISION,
            overall_score=70,
            consolidated_findings=[finding],
        )

        sarif_doc = SarifExporter.to_sarif(report)
        self.assertEqual(sarif_doc["version"], "2.1.0")
        self.assertEqual(len(sarif_doc["runs"]), 1)
        run = sarif_doc["runs"][0]
        self.assertEqual(run["tool"]["driver"]["name"], "PanelReview")
        self.assertEqual(len(run["results"]), 1)
        self.assertEqual(run["results"][0]["level"], "error")
        self.assertEqual(run["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"], "app.py")


if __name__ == "__main__":
    unittest.main()
