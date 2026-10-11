import unittest
from panel_review.presets import PRESETS, apply_preset


class TestPresets(unittest.TestCase):
    def test_presets_exist(self):
        self.assertIn("security-strict", PRESETS)
        self.assertIn("sre-readiness", PRESETS)
        self.assertIn("full-audit", PRESETS)

    def test_apply_preset(self):
        config_dict = {
            "personas": [
                {"id": "security", "enabled": True},
                {"id": "observability", "enabled": True},
                {"id": "performance", "enabled": True},
            ],
            "consensus": {
                "min_approval_score": 75,
                "critical_issues_block_approval": True,
            }
        }
        res = apply_preset(config_dict, "security-strict")
        # In security-strict, only security & compliance are active
        sec = next(p for p in res["personas"] if p["id"] == "security")
        perf = next(p for p in res["personas"] if p["id"] == "performance")
        self.assertTrue(sec["enabled"])
        self.assertFalse(perf["enabled"])


if __name__ == "__main__":
    unittest.main()
