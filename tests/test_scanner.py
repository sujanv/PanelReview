import unittest
import os
from panel_review.scanner.language_detect import detect_language
from panel_review.scanner.repo_scanner import RepoScanner


class TestScanner(unittest.TestCase):
    def test_detect_language(self):
        self.assertEqual(detect_language("main.py"), "Python")
        self.assertEqual(detect_language("service.go"), "Go")
        self.assertEqual(detect_language("server.ts"), "TypeScript")
        self.assertEqual(detect_language("Dockerfile"), "Dockerfile")
        self.assertEqual(detect_language("script.sh"), "Shell")
        self.assertEqual(detect_language("lib.rs"), "Rust")

    def test_repo_scanner_local(self):
        scanner = RepoScanner()
        repo_info = scanner.scan_directory("examples/sample_polyglot_project")
        self.assertGreaterEqual(repo_info.total_files, 3)
        self.assertIn("Python", repo_info.languages)
        self.assertIn("Go", repo_info.languages)
        self.assertIn("TypeScript", repo_info.languages)


if __name__ == "__main__":
    unittest.main()
