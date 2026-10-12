import unittest
from scripts.staged_git_pusher import generate_commit_message, run_staged_push


class TestStagedPusher(unittest.TestCase):
    def test_commit_message_mapping(self):
        msg = generate_commit_message("panel_config.yaml")
        self.assertIn("config", msg)

        msg2 = generate_commit_message("panel_review/personas/security.py")
        self.assertIn("Security Engineer", msg2)

    def test_dry_run_staged_push(self):
        # Dry run should succeed with return code 0 and change no git state
        code = run_staged_push(dry_run=True, instant=True)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
