import unittest
from panel_review.providers.mock_provider import MockProvider
from panel_review.providers.factory import ProviderFactory
from panel_review.config import PanelConfig


class TestProviders(unittest.TestCase):
    def test_mock_provider_security_generation(self):
        prov = MockProvider()
        resp = prov.generate("File: app.py\npassword = 'supersecretpass'", system_prompt="You are a Security Engineer")
        self.assertIn("Hardcoded", resp)
        self.assertIn("findings", resp)

    def test_provider_factory_mock(self):
        cfg = PanelConfig(default_provider="mock")
        prov = ProviderFactory.create("mock", cfg)
        self.assertIsInstance(prov, MockProvider)
        test_res = prov.test_connection()
        self.assertEqual(test_res["status"], "success")


if __name__ == "__main__":
    unittest.main()
