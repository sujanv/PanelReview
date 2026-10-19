"""
Policy-as-Code Rules and Data Models.
Defines organizational guardrails, rule categories, and violation models.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Pattern
import re


class PolicySeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class PolicyCategory(str, Enum):
    SECURITY = "SECURITY"
    OBSERVABILITY = "OBSERVABILITY"
    ARCHITECTURE = "ARCHITECTURE"
    QUALITY = "QUALITY"
    COMPLIANCE = "COMPLIANCE"


@dataclass
class PolicyRule:
    """Represents an individual organizational policy rule."""
    id: str
    name: str
    description: str
    category: PolicyCategory
    severity: PolicySeverity
    pattern: Optional[str] = None
    file_extensions: List[str] = field(default_factory=list)  # Empty means all code files
    exclude_paths: List[str] = field(default_factory=lambda: ["tests/", "examples/", "test_"])
    remediation: str = ""
    enabled: bool = True
    _compiled: Optional[Pattern] = field(default=None, init=False, repr=False)

    def matches(self, line: str, file_path: str) -> bool:
        """Determines if a given line violates this policy rule."""
        if not self.enabled or not self.pattern:
            return False

        # Check path exclusion
        for exc in self.exclude_paths:
            if exc in file_path:
                return False

        # Check file extension filter
        if self.file_extensions:
            matched_ext = any(file_path.endswith(ext) for ext in self.file_extensions)
            if not matched_ext:
                return False

        if self._compiled is None:
            self._compiled = re.compile(self.pattern, re.IGNORECASE)

        return bool(self._compiled.search(line))


@dataclass
class PolicyViolation:
    """Represents a concrete detected policy violation."""
    rule_id: str
    rule_name: str
    category: PolicyCategory
    severity: PolicySeverity
    file_path: str
    line_number: int
    snippet: str
    remediation: str

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "category": self.category.value,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "snippet": self.snippet.strip(),
            "remediation": self.remediation,
        }


# Standard built-in organizational guardrail rules
DEFAULT_POLICY_RULES: List[PolicyRule] = [
    PolicyRule(
        id="POL-SEC-001",
        name="No Insecure HTTP Endpoints",
        description="Plain unencrypted HTTP URLs detected in production source code.",
        category=PolicyCategory.SECURITY,
        severity=PolicySeverity.HIGH,
        pattern=r'http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0|schemas\.|www\.w3\.org)[a-zA-Z0-9.-]+',
        remediation="Upgrade the endpoint to encrypted HTTPS (https://) to ensure in-transit TLS encryption.",
    ),
    PolicyRule(
        id="POL-SEC-002",
        name="Dangerous Code Execution Invocation",
        description="Dynamic string evaluation or unsafe shell execution functions detected.",
        category=PolicyCategory.SECURITY,
        severity=PolicySeverity.CRITICAL,
        pattern=r'\b(eval\(|exec\(|shell\s*=\s*True)\b',
        file_extensions=[".py", ".js", ".ts"],
        remediation="Avoid dynamic code evaluation. Use parameterized subprocess calls with shell=False.",
    ),
    PolicyRule(
        id="POL-OBS-001",
        name="Unstructured Console Logging in Backend Services",
        description="Direct stdout/console prints used instead of structured logger with levels and tracing.",
        category=PolicyCategory.OBSERVABILITY,
        severity=PolicySeverity.MEDIUM,
        pattern=r'^\s*(print\(|console\.log\(|fmt\.Println\()',
        file_extensions=[".py", ".js", ".ts", ".go"],
        exclude_paths=["tests/", "examples/", "cli.py", "scripts/", "main.go"],
        remediation="Replace ad-hoc print calls with a structured logger (logging, pino, zerolog, zap).",
    ),
    PolicyRule(
        id="POL-ARCH-001",
        name="Hardcoded Private or Public IPv4 Address",
        description="Raw hardcoded IP address string embedded in source code.",
        category=PolicyCategory.ARCHITECTURE,
        severity=PolicySeverity.MEDIUM,
        pattern=r'\b(?:10|172\.(?:1[6-9]|2[0-9]|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b',
        remediation="Extract IP addresses to environment configuration or DNS hostnames.",
    ),
    PolicyRule(
        id="POL-QUAL-001",
        name="Unresolved TODO/FIXME in Core Logic",
        description="Technical debt marker identified in production logic without tracking issue.",
        category=PolicyCategory.QUALITY,
        severity=PolicySeverity.LOW,
        pattern=r'//\s*(?:TODO|FIXME|BUG)\b|#\s*(?:TODO|FIXME|BUG)\b',
        exclude_paths=["tests/"],
        remediation="Resolve technical debt or link with a dedicated issue tracker ticket.",
    ),
]
