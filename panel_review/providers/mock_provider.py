"""
Offline / Mock rule-based provider for testing, demos, and air-gapped environments.
Simulates realistic LLM responses tailored to each persona and repository content.
"""

import json
import re
from typing import Optional
from panel_review.providers.base import LLMProvider


class MockProvider(LLMProvider):
    def __init__(
        self,
        model: str = "mock-expert-v1",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        timeout_seconds: int = 5,
    ):
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
        )

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        sys_p = (system_prompt or "").lower()
        prompt_lower = prompt.lower()

        # Check if this is the Panel Chair consensus synthesis
        if "consensus" in sys_p or "chair" in sys_p or "panel chair" in prompt_lower:
            return self._generate_chair_consensus(prompt)

        # Match persona precisely from the persona declaration on the first line
        first_line = sys_p.splitlines()[0] if sys_p else ""
        if "observability" in first_line:
            return self._generate_observability_review(prompt)
        elif "performance" in first_line:
            return self._generate_performance_review(prompt)
        elif "architect" in first_line:
            return self._generate_architecture_review(prompt)
        elif "qa" in first_line:
            return self._generate_qa_review(prompt)
        elif "compliance" in first_line:
            return self._generate_compliance_review(prompt)
        elif "security" in first_line:
            return self._generate_security_review(prompt)
        else:
            return self._generate_generic_review(prompt)

    def _generate_security_review(self, prompt: str) -> str:
        findings = []
        score = 88

        # Heuristic checks on the prompt content
        if re.search(r"password\s*=\s*['\"][^'\"]+['\"]|api_key\s*=\s*['\"][^'\"]+['\"]|secret\s*=\s*['\"][^'\"]+['\"]", prompt, re.I):
            findings.append({
                "title": "Potential Hardcoded Credentials or API Keys Detected",
                "severity": "CRITICAL",
                "file_path": self._extract_first_file(prompt),
                "line_number": 12,
                "description": "Sensitive credentials or secrets appear hardcoded in source files rather than managed via environment variables or secret vaults.",
                "recommendation": "Migrate secrets to environment variables or secret managers (e.g. AWS Secrets Manager, HashiCorp Vault).",
                "category": "CWE-798: Use of Hard-coded Credentials"
            })
            score -= 25

        if re.search(r"exec\(|eval\(|shell\s*=\s*True|system\(", prompt):
            findings.append({
                "title": "Unsafe Dynamic Code or Command Execution",
                "severity": "HIGH",
                "file_path": self._extract_first_file(prompt),
                "line_number": 24,
                "description": "Direct execution of dynamic strings or shell commands can lead to arbitrary code execution / command injection.",
                "recommendation": "Avoid shell=True and dynamic eval. Use parameterized argument lists with subprocess.run(..., shell=False).",
                "category": "CWE-78: OS Command Injection"
            })
            score -= 20

        if not findings:
            findings.append({
                "title": "Verify Input Sanitization and Parameterized Queries",
                "severity": "LOW",
                "file_path": self._extract_first_file(prompt),
                "line_number": 1,
                "description": "Ensure all external inputs from HTTP requests or user inputs are strictly validated with type schemas and parameterized queries.",
                "recommendation": "Use strict schema validators (e.g., Pydantic, Zod, or validator middleware) across all public endpoints.",
                "category": "Input Validation"
            })

        return json.dumps({
            "summary": "Security analysis identified key authorization, input validation, and credential posture factors.",
            "score": max(20, score),
            "findings": findings
        }, indent=2)

    def _generate_observability_review(self, prompt: str) -> str:
        findings = []
        score = 82

        if re.search(r"except\s*:\s*pass|catch\s*\([^)]*\)\s*\{\s*\}", prompt):
            findings.append({
                "title": "Silent Error Suppression / Swallowed Exceptions",
                "severity": "HIGH",
                "file_path": self._extract_first_file(prompt),
                "line_number": 18,
                "description": "Exceptions are caught and suppressed without logging or metric increments, blinding operators to production anomalies.",
                "recommendation": "Log caught exceptions with stack traces and emit error counter metrics.",
                "category": "Error Telemetry"
            })
            score -= 20

        if not re.search(r"trace_id|correlation_id|opentelemetry|span", prompt, re.I):
            findings.append({
                "title": "Lack of Distributed Trace Context Propagation",
                "severity": "MEDIUM",
                "file_path": self._extract_first_file(prompt),
                "line_number": 5,
                "description": "No OpenTelemetry trace or correlation ID headers detected in log outputs or inter-service requests.",
                "recommendation": "Adopt structured logging with OpenTelemetry trace_id and span_id injected into log records.",
                "category": "Distributed Tracing"
            })
            score -= 10

        findings.append({
            "title": "Ensure Network Call Timeouts on External I/O",
            "severity": "MEDIUM",
            "file_path": self._extract_first_file(prompt),
            "line_number": 10,
            "description": "Outbound HTTP or socket operations should explicitly configure connection and read timeouts to prevent thread pool exhaustion.",
            "recommendation": "Specify explicit timeout values on all HTTP/TCP client invocations.",
            "category": "Resilience & SRE"
        })

        return json.dumps({
            "summary": "Observability review analyzed telemetry instrumentation, structured logging, and resilience controls.",
            "score": max(30, score),
            "findings": findings
        }, indent=2)

    def _generate_performance_review(self, prompt: str) -> str:
        findings = []
        score = 85

        if re.search(r"for\s+.*:\s*\n\s+for\s+.*:", prompt):
            findings.append({
                "title": "Nested Iteration With Potential O(N^2) Complexity",
                "severity": "MEDIUM",
                "file_path": self._extract_first_file(prompt),
                "line_number": 15,
                "description": "Nested loops iterating over collections without indexing or map lookups may degrade throughput under large inputs.",
                "recommendation": "Transform inner lookups into dictionary/hash-set lookups for O(1) amortized access.",
                "category": "Algorithmic Efficiency"
            })
            score -= 15

        findings.append({
            "title": "Resource Handle Lifecycle and Connection Pooling",
            "severity": "LOW",
            "file_path": self._extract_first_file(prompt),
            "line_number": 1,
            "description": "Ensure file handles, database connections, and HTTP clients utilize connection pooling and context managers (with/defer).",
            "recommendation": "Reuse persistent clients and ensure context manager cleanup.",
            "category": "Resource Management"
        })

        return json.dumps({
            "summary": "Performance evaluation reviewed algorithmic complexity, memory allocation patterns, and connection lifecycle.",
            "score": max(30, score),
            "findings": findings
        }, indent=2)

    def _generate_architecture_review(self, prompt: str) -> str:
        findings = [
            {
                "title": "Decouple External Dependencies via Clean Interfaces",
                "severity": "LOW",
                "file_path": self._extract_first_file(prompt),
                "line_number": 1,
                "description": "Components should depend on abstractions/protocols rather than concrete implementations to facilitate dependency injection and test isolation.",
                "recommendation": "Define clear interface boundaries (Abstract Base Classes, Protocols, or interfaces) for external providers and storage engines.",
                "category": "SOLID / Architecture"
            }
        ]
        return json.dumps({
            "summary": "Architectural review assessed modularity, separation of concerns, and abstraction boundaries.",
            "score": 90,
            "findings": findings
        }, indent=2)

    def _generate_qa_review(self, prompt: str) -> str:
        findings = [
            {
                "title": "Ensure Edge-Case and Negative Testing for Error Paths",
                "severity": "MEDIUM",
                "file_path": self._extract_first_file(prompt),
                "line_number": 1,
                "description": "Verify comprehensive test coverage for non-happy path conditions, such as network timeouts, invalid inputs, and unexpected empty responses.",
                "recommendation": "Add automated unit tests mocking failure responses and asserting defensive fallback behavior.",
                "category": "Test Reliability"
            }
        ]
        return json.dumps({
            "summary": "QA evaluation focused on test isolation, deterministic test behavior, and boundary coverage.",
            "score": 86,
            "findings": findings
        }, indent=2)

    def _generate_compliance_review(self, prompt: str) -> str:
        findings = [
            {
                "title": "Verify PII Redaction in Operational Logs",
                "severity": "LOW",
                "file_path": self._extract_first_file(prompt),
                "line_number": 1,
                "description": "Ensure user emails, account identifiers, or personally identifiable data are not emitted in cleartext to log sinks.",
                "recommendation": "Implement an automated log masking interceptor for sensitive user attributes.",
                "category": "GDPR / Privacy"
            }
        ]
        return json.dumps({
            "summary": "Compliance review validated privacy safeguards and data governance guidelines.",
            "score": 92,
            "findings": findings
        }, indent=2)

    def _generate_chair_consensus(self, prompt: str) -> str:
        return json.dumps({
            "executive_summary": "The Panel Review Board has convened and completed an evaluation across Security, Observability, Performance, Architecture, QA, and Compliance disciplines. The repository displays solid baseline engineering with actionable recommendations around structured telemetry, error propagation, and defensive input validation.",
            "overall_score": 84,
            "verdict": "APPROVED_WITH_CONDITIONS",
            "action_items": [
                "Implement structured logging with OpenTelemetry trace and correlation ID propagation.",
                "Eliminate any silent error suppression and ensure outbound I/O timeouts are strictly defined.",
                "Audit external endpoints to ensure schema validation and sanitized input boundaries.",
                "Expand automated unit tests covering negative error response handling."
            ]
        }, indent=2)

    def _generate_generic_review(self, prompt: str) -> str:
        return json.dumps({
            "summary": "General code review assessment.",
            "score": 88,
            "findings": [
                {
                    "title": "General Code Health Inspection",
                    "severity": "INFO",
                    "file_path": self._extract_first_file(prompt),
                    "line_number": 1,
                    "description": "Code follows standard conventions.",
                    "recommendation": "Continue following idiomatic style guides.",
                    "category": "Code Quality"
                }
            ]
        }, indent=2)

    def _extract_first_file(self, prompt: str) -> str:
        match = re.search(r"File:\s*([^\s\n\r]+)", prompt)
        if match:
            return match.group(1)
        return "main.py"
