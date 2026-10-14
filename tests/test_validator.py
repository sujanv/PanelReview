import unittest
from panel_review.config import PanelConfig, ProviderConfig, PersonaConfig
from panel_review.validator import ConfigValidator


class TestValidator(unittest.TestCase):
    def test_valid_config(self):
        cfg = PanelConfig(
            default_provider="mock",
            default_model="mock-expert-v1",
            providers={"mock": ProviderConfig(name="mock", model="mock-expert-v1")},
            personas=[PersonaConfig(id="security", name="Security Engineer")],
        )
        report = ConfigValidator.validate(cfg)
        self.assertTrue(report.is_valid)

    def test_duplicate_persona_id(self):
        cfg = PanelConfig(
            default_provider="mock",
            default_model="mock-expert-v1",
            providers={"mock": ProviderConfig(name="mock", model="mock-expert-v1")},
            personas=[
                PersonaConfig(id="security", name="Security 1"),
                PersonaConfig(id="security", name="Security 2"),
            ],
        )
        report = ConfigValidator.validate(cfg)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("Duplicate" in issue.message for issue in report.issues))


if __name__ == "__main__":
    unittest.main()
