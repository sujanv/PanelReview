import unittest
from panel_review.config import load_config
from panel_review.scanner.repo_scanner import RepoScanner
from panel_review.engine.reviewer import ReviewEngine
from panel_review.engine.report import ReportGenerator


class TestEngine(unittest.TestCase):
    def test_end_to_end_panel_review(self):
        config = load_config()
        config.default_provider = "mock"

        scanner = RepoScanner(config.scanner)
        repo_info = scanner.scan_directory("examples/sample_polyglot_project")

        engine = ReviewEngine(config)
        report = engine.run_review(repo_info)

        self.assertIsNotNone(report)
        self.assertGreater(len(report.persona_results), 0)
        self.assertGreater(report.overall_score, 0)
        self.assertIsNotNone(report.overall_verdict)

        # Test report generation
        md = ReportGenerator.to_markdown(report)
        self.assertIn("AI Agent Panel Review Report", md)

        html = ReportGenerator.to_html(report)
        self.assertIn("AI Agent Panel Review Report", html)

        json_str = ReportGenerator.to_json(report)
        self.assertIn("overall_score", json_str)


if __name__ == "__main__":
    unittest.main()
