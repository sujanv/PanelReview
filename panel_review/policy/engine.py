"""
Policy-as-Code Evaluation Engine.
Evaluates repository files against configurable organizational guardrails.
"""

import os
import json
from typing import List, Dict, Optional
from panel_review.policy.rules import PolicyRule, PolicyViolation, DEFAULT_POLICY_RULES, PolicySeverity, PolicyCategory


class PolicyEngine:
    """Evaluates source code repositories against active guardrail rules."""

    def __init__(self, custom_rules: Optional[List[PolicyRule]] = None):
        self.rules: List[PolicyRule] = custom_rules if custom_rules is not None else list(DEFAULT_POLICY_RULES)

    @classmethod
    def from_config_file(cls, config_path: str) -> "PolicyEngine":
        """Loads policy rules from a JSON or YAML file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Policy file not found: {config_path}")

        rules = []
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()

        if config_path.endswith((".yaml", ".yml")):
            try:
                import yaml
                data = yaml.safe_load(content) or {}
            except ImportError:
                # Basic JSON-compatible YAML parsing fallback
                try:
                    data = json.loads(content)
                except Exception:
                    data = {}
        else:
            data = json.loads(content)

        raw_rules = data.get("rules", [])
        for r in raw_rules:
            try:
                cat = PolicyCategory[r.get("category", "QUALITY").upper()]
                sev = PolicySeverity[r.get("severity", "MEDIUM").upper()]
                rule = PolicyRule(
                    id=r["id"],
                    name=r["name"],
                    description=r.get("description", ""),
                    category=cat,
                    severity=sev,
                    pattern=r.get("pattern"),
                    file_extensions=r.get("file_extensions", []),
                    exclude_paths=r.get("exclude_paths", ["tests/"]),
                    remediation=r.get("remediation", ""),
                    enabled=r.get("enabled", True),
                )
                rules.append(rule)
            except Exception:
                continue

        return cls(custom_rules=rules if rules else list(DEFAULT_POLICY_RULES))

    def evaluate_file(self, file_path: str, content: str) -> List[PolicyViolation]:
        """Scans a single file's content against all active policy rules."""
        violations: List[PolicyViolation] = []
        lines = content.splitlines()

        for line_idx, line in enumerate(lines, 1):
            for rule in self.rules:
                if rule.matches(line, file_path):
                    violations.append(
                        PolicyViolation(
                            rule_id=rule.id,
                            rule_name=rule.name,
                            category=rule.category,
                            severity=rule.severity,
                            file_path=file_path,
                            line_number=line_idx,
                            snippet=line.strip(),
                            remediation=rule.remediation,
                        )
                    )

        return violations

    def evaluate_repository(self, file_contents: Dict[str, str]) -> Dict:
        """Evaluates a dictionary of {file_path: content} and returns violation metrics."""
        all_violations: List[PolicyViolation] = []

        for fpath, content in file_contents.items():
            violations = self.evaluate_file(fpath, content)
            all_violations.extend(violations)

        severity_counts = {sev.value: 0 for sev in PolicySeverity}
        category_counts = {cat.value: 0 for cat in PolicyCategory}

        for v in all_violations:
            severity_counts[v.severity.value] += 1
            category_counts[v.category.value] += 1

        passed = severity_counts[PolicySeverity.CRITICAL.value] == 0 and severity_counts[PolicySeverity.HIGH.value] == 0

        return {
            "passed": passed,
            "total_violations": len(all_violations),
            "severity_counts": severity_counts,
            "category_counts": category_counts,
            "violations": [v.to_dict() for v in all_violations],
        }
