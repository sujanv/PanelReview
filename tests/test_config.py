import unittest
import os
import json
from panel_review.config import load_config, PanelConfig


class TestConfig(unittest.TestCase):
    def test_load_default_config(self):
        config = load_config()
        self.assertIsInstance(config, PanelConfig)
        self.assertIn(config.default_provider, ["mock", "openai", "anthropic", "gemini", "ollama"])
        self.assertGreater(len(config.personas), 0)

    def test_persona_provider_resolution(self):
        config = load_config()
        for persona in config.get_enabled_personas():
            prov, model = config.get_persona_provider(persona)
            self.assertIsNotNone(prov)
            self.assertIsNotNone(model)

    def test_scanner_config(self):
        config = load_config()
        self.assertGreater(config.scanner.max_file_size_kb, 0)
        self.assertIn(".git", config.scanner.exclude_dirs)


if __name__ == "__main__":
    unittest.main()
