import unittest
from panel_review.personas.security import SecurityEngineerPersona
from panel_review.personas.observability import ObservabilityEngineerPersona
from panel_review.personas.performance import PerformanceEngineerPersona
from panel_review.personas.architecture import SoftwareArchitectPersona
from panel_review.personas.qa import QAEngineerPersona
from panel_review.personas.compliance import ComplianceEngineerPersona
from panel_review.personas.chair import PanelChair
from panel_review.models import SeverityLevel, ReviewVerdict, RepositoryInfo, ScannedFile


class TestPersonas(unittest.TestCase):
    def test_security_persona_prompt_and_parse(self):
        persona = SecurityEngineerPersona()
        sys_prompt = persona.build_system_prompt()
        self.assertIn("Security Engineer", sys_prompt)
        self.assertIn("OWASP", sys_prompt)

        # Test parsing valid JSON response
        sample_json = """```json
        {
            "summary": "Found critical credential exposure.",
            "score": 45,
            "findings": [
                {
                    "title": "Hardcoded AWS secret",
                    "severity": "CRITICAL",
                    "file_path": "app.py",
                    "line_number": 10,
                    "description": "AWS secret exposed in cleartext",
                    "recommendation": "Use AWS IAM roles"
                }
            ]
        }
        ```"""
        result = persona.parse_llm_response(sample_json, "test-model")
        self.assertEqual(result.persona_id, "security")
        self.assertEqual(result.score, 45)
        self.assertEqual(result.verdict, ReviewVerdict.REJECTED)
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].severity, SeverityLevel.CRITICAL)

    def test_observability_persona(self):
        persona = ObservabilityEngineerPersona()
        sys_prompt = persona.build_system_prompt()
        self.assertIn("Observability & SRE", sys_prompt)

    def test_panel_chair_consensus(self):
        chair = PanelChair()
        repo = RepositoryInfo(source="test_repo", is_remote=False)
        sec = SecurityEngineerPersona().parse_llm_response('{"summary": "ok", "score": 95, "findings": []}')
        obs = ObservabilityEngineerPersona().parse_llm_response('{"summary": "ok", "score": 90, "findings": []}')

        report = chair.synthesize(repo, [sec, obs])
        self.assertEqual(report.overall_verdict, ReviewVerdict.APPROVED)
        self.assertGreaterEqual(report.overall_score, 90)


if __name__ == "__main__":
    unittest.main()
