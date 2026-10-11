"""
Review Presets system for one-click specialized panel configurations.
"""

from typing import Dict, List, Any


PRESETS: Dict[str, Dict[str, Any]] = {
    "security-strict": {
        "description": "High-rigor security and compliance audit with zero tolerance for critical issues.",
        "active_persona_ids": ["security", "compliance"],
        "min_approval_score": 85,
        "critical_issues_block_approval": True,
    },
    "sre-readiness": {
        "description": "Production readiness assessment emphasizing telemetry, timeouts, and latency.",
        "active_persona_ids": ["observability", "performance"],
        "min_approval_score": 80,
        "critical_issues_block_approval": True,
    },
    "clean-architecture": {
        "description": "Modularity, maintainability, design patterns, and testability review.",
        "active_persona_ids": ["architecture", "qa"],
        "min_approval_score": 75,
        "critical_issues_block_approval": False,
    },
    "quick-scan": {
        "description": "Fast evaluation focusing strictly on top vulnerabilities and crashes.",
        "active_persona_ids": ["security", "qa"],
        "min_approval_score": 70,
        "critical_issues_block_approval": True,
    },
    "full-audit": {
        "description": "Comprehensive board review across all 6 specialist personas.",
        "active_persona_ids": ["security", "observability", "performance", "architecture", "qa", "compliance"],
        "min_approval_score": 75,
        "critical_issues_block_approval": True,
    },
}


def apply_preset(config_dict: Dict[str, Any], preset_name: str) -> Dict[str, Any]:
    """
    Applies a named preset to a panel configuration dictionary.
    """
    if preset_name not in PRESETS:
        return config_dict

    preset = PRESETS[preset_name]
    active_ids = set(preset["active_persona_ids"])

    if "personas" in config_dict:
        for p in config_dict["personas"]:
            p["enabled"] = p.get("id") in active_ids

    if "consensus" in config_dict:
        config_dict["consensus"]["min_approval_score"] = preset["min_approval_score"]
        config_dict["consensus"]["critical_issues_block_approval"] = preset["critical_issues_block_approval"]

    return config_dict
