import unittest
from panel_review.scanner.secret_scanner import SecretScanner, calculate_shannon_entropy, mask_secret
from panel_review.models import SeverityLevel


class TestSecretScanner(unittest.TestCase):
    def test_detect_aws_key(self):
        content = "AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'\nAWS_SECRET = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'"
        findings = SecretScanner.scan_file_content("config.py", content)
        self.assertGreaterEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, SeverityLevel.CRITICAL)
        self.assertIn("AWS", findings[0].title)

    def test_mask_secret(self):
        masked = mask_secret("AKIAIOSFODNN7EXAMPLE")
        self.assertEqual(masked[:4], "AKIA")
        self.assertEqual(masked[-4:], "MPLE")
        self.assertIn("****", masked)

    def test_shannon_entropy(self):
        low_ent = calculate_shannon_entropy("aaaaaaaaaaaa")
        high_ent = calculate_shannon_entropy("gK8#mQ2$xP9!vL5@wR4^")
        self.assertGreater(high_ent, low_ent)
        self.assertGreater(high_ent, 4.0)


if __name__ == "__main__":
    unittest.main()
