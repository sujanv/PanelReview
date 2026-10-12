import unittest
from panel_review.models import ReviewFinding, SeverityLevel
from panel_review.engine.remediator import PatchRemediator


class TestRemediator(unittest.TestCase):
    def test_generate_patch(self):
        finding = ReviewFinding(
            title="Missing HTTP Timeout",
            severity=SeverityLevel.MEDIUM,
            file_path="service.py",
            line_number=2,
            description="Outbound call lacks timeout",
            recommendation="Add timeout=10.0",
            category="Resilience",
            persona_id="observability",
        )
        sample_code = "import requests\nresp = requests.get('https://api.example.com')\n"
        patch = PatchRemediator.generate_patch_for_finding(finding, sample_code)

        self.assertIsNotNone(patch)
        self.assertIn("--- a/service.py", patch.unified_diff)
        self.assertIn("+++ b/service.py", patch.unified_diff)


if __name__ == "__main__":
    unittest.main()
