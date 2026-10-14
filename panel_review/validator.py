"""
Configuration Schema Validator and Environment Linter.
Validates panel review configuration, checks API key availability, and reports misconfigurations.
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any
from panel_review.config import PanelConfig, load_config


@dataclass
class ValidationIssue:
    level: str  # "ERROR" or "WARNING"
    field: str
    message: str


@dataclass
class ValidationReport:
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)

    def print_diagnostics(self):
        print("\n🔍 PanelReview Configuration Validation Report:")
        if not self.issues:
            print("  ✅ Configuration is valid with zero issues detected!\n")
            return

        for issue in self.issues:
            icon = "❌" if issue.level == "ERROR" else "⚠️"
            print(f"  {icon} [{issue.level}] {issue.field}: {issue.message}")
        print()


class ConfigValidator:
    @staticmethod
    def validate(config: PanelConfig) -> ValidationReport:
        issues: List[ValidationIssue] = []

        # Validate Default Provider
        if config.default_provider not in config.providers and config.default_provider != "mock":
            issues.append(ValidationIssue(
                level="ERROR",
                field="default_provider",
                message=f"Default provider '{config.default_provider}' is not defined in 'providers' dictionary.",
            ))

        # Validate Providers & API Keys
        for prov_name, prov_cfg in config.providers.items():
            if not prov_cfg.model:
                issues.append(ValidationIssue(
                    level="ERROR",
                    field=f"providers.{prov_name}.model",
                    message="Model name cannot be empty.",
                ))
            if prov_cfg.api_key_env:
                if not os.getenv(prov_cfg.api_key_env):
                    issues.append(ValidationIssue(
                        level="WARNING",
                        field=f"providers.{prov_name}.api_key_env",
                        message=f"Environment variable '{prov_cfg.api_key_env}' is not currently set in environment.",
                    ))

        # Validate Personas
        seen_ids = set()
        for p in config.personas:
            if not p.id:
                issues.append(ValidationIssue(
                    level="ERROR",
                    field="personas[].id",
                    message="Persona ID must not be empty.",
                ))
            elif p.id in seen_ids:
                issues.append(ValidationIssue(
                    level="ERROR",
                    field=f"personas[{p.id}]",
                    message=f"Duplicate persona ID '{p.id}'. Each persona must have a unique ID.",
                ))
            seen_ids.add(p.id)

            if p.severity_threshold not in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
                issues.append(ValidationIssue(
                    level="WARNING",
                    field=f"personas[{p.id}].severity_threshold",
                    message=f"Unknown threshold '{p.severity_threshold}'. Defaulting to 'LOW'.",
                ))

        has_errors = any(i.level == "ERROR" for i in issues)
        return ValidationReport(is_valid=not has_errors, issues=issues)
