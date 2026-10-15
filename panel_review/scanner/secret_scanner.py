"""
High-performance Secret and Credential Scanner for Polyglot Codebases.
Uses signature regexes and Shannon entropy analysis to detect leaked tokens, API keys, and certificates.
"""

import math
import re
from typing import List, Dict, Optional, Tuple, Any
from panel_review.models import ReviewFinding, SeverityLevel


# Signatures for known secret and credential patterns
SECRET_PATTERNS: List[Dict[str, Any]] = [
    {
        "name": "AWS Access Key ID",
        "pattern": re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        "severity": SeverityLevel.CRITICAL,
        "category": "CWE-798: Hardcoded AWS Credentials",
    },
    {
        "name": "AWS Secret Access Key",
        "pattern": re.compile(r"(?i)aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/+=]{40}['\"]"),
        "severity": SeverityLevel.CRITICAL,
        "category": "CWE-798: Hardcoded AWS Credentials",
    },
    {
        "name": "GitHub Personal Access Token",
        "pattern": re.compile(r"\b(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82})\b"),
        "severity": SeverityLevel.CRITICAL,
        "category": "CWE-798: Hardcoded GitHub Token",
    },
    {
        "name": "Generic Private Key",
        "pattern": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
        "severity": SeverityLevel.CRITICAL,
        "category": "CWE-312: Cleartext Private Key Exposure",
    },
    {
        "name": "Slack Webhook URL",
        "pattern": re.compile(r"https://hooks\.slack\.com/services/T[A-Za-z0-9]+/B[A-Za-z0-9]+/[A-Za-z0-9]+"),
        "severity": SeverityLevel.HIGH,
        "category": "CWE-798: Hardcoded Slack Webhook",
    },
    {
        "name": "Stripe Live Secret Key",
        "pattern": re.compile(r"\b(sk_live_[0-9a-zA-Z]{24})\b"),
        "severity": SeverityLevel.CRITICAL,
        "category": "CWE-798: Hardcoded Stripe API Key",
    },
    {
        "name": "Database Connection String with Credentials",
        "pattern": re.compile(r"\b(?:postgres|postgresql|mysql|mongodb|redis)://[^:\s]+:[^@\s]+@[^\s/]+"),
        "severity": SeverityLevel.CRITICAL,
        "category": "CWE-798: Embedded Database Credentials",
    },
    {
        "name": "JWT (JSON Web Token)",
        "pattern": re.compile(r"\beyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+\b"),
        "severity": SeverityLevel.MEDIUM,
        "category": "CWE-312: Hardcoded JWT Session Token",
    },
]


def calculate_shannon_entropy(data: str) -> float:
    """Calculates Shannon entropy to detect high-randomness secret strings."""
    if not data:
        return 0.0
    entropy = 0.0
    for x in set(data):
        p_x = float(data.count(x)) / len(data)
        entropy += - p_x * math.log2(p_x)
    return entropy


def mask_secret(secret_text: str) -> str:
    """Safely masks secret text so it never leaks in reports."""
    if len(secret_text) <= 8:
        return "********"
    return secret_text[:4] + "*" * (len(secret_text) - 8) + secret_text[-4:]


class SecretScanner:
    @staticmethod
    def scan_file_content(file_path: str, content: str) -> List[ReviewFinding]:
        findings: List[ReviewFinding] = []
        lines = content.splitlines()

        for line_idx, line in enumerate(lines, 1):
            # Check pattern signatures
            for rule in SECRET_PATTERNS:
                matches = rule["pattern"].findall(line)
                if matches:
                    raw_val = matches[0] if isinstance(matches[0], str) else matches[0][0]
                    masked = mask_secret(raw_val)
                    findings.append(ReviewFinding(
                        title=f"Exposed {rule['name']}",
                        severity=rule["severity"],
                        file_path=file_path,
                        line_number=line_idx,
                        description=f"Detected sensitive {rule['name']} ({masked}) committed in source code.",
                        recommendation="Immediately revoke this credential and migrate to an environment variable or secret vault (e.g., AWS Secrets Manager, HashiCorp Vault).",
                        code_snippet=line.strip().replace(raw_val, masked),
                        category=rule["category"],
                        persona_id="security",
                    ))

            # High entropy heuristic for potential API keys in assignments
            if "=" in line and not line.strip().startswith(("#", "//", "/*", "*")):
                parts = line.split("=", 1)
                val_part = parts[1].strip().strip("'\";,")
                if len(val_part) >= 24 and " " not in val_part:
                    entropy = calculate_shannon_entropy(val_part)
                    if entropy > 4.5:
                        masked = mask_secret(val_part)
                        findings.append(ReviewFinding(
                            title="High-Entropy String (Suspected Secret or Key)",
                            severity=SeverityLevel.HIGH,
                            file_path=file_path,
                            line_number=line_idx,
                            description=f"Variable assignment contains high-entropy string (entropy: {entropy:.2f}) resembling an API key: {masked}",
                            recommendation="Ensure this string is not an API key or private secret. Store sensitive values in environment variables.",
                            code_snippet=line.strip().replace(val_part, masked),
                            category="CWE-798: High Entropy Secret",
                            persona_id="security",
                        ))

        return findings
