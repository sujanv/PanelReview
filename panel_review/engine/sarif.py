"""
SARIF (Static Analysis Results Interchange Format) v2.1.0 Exporter.
Allows PanelReview findings to integrate with GitHub Code Scanning, GitLab SAST, and IDEs.
"""

import json
from typing import Dict, Any, List
from panel_review.models import ConsensusReport, ReviewFinding, SeverityLevel


class SarifExporter:
    @staticmethod
    def to_sarif(report: ConsensusReport) -> Dict[str, Any]:
        """
        Converts ConsensusReport into standard SARIF v2.1.0 JSON format.
        """
        rules_map: Dict[str, Dict[str, Any]] = {}
        results: List[Dict[str, Any]] = []

        level_map = {
            SeverityLevel.CRITICAL: "error",
            SeverityLevel.HIGH: "error",
            SeverityLevel.MEDIUM: "warning",
            SeverityLevel.LOW: "note",
            SeverityLevel.INFO: "note",
        }

        for finding in report.consolidated_findings:
            rule_id = f"PANEL-{finding.persona_id.upper()}-{hash(finding.title) % 10000:04d}"

            if rule_id not in rules_map:
                rules_map[rule_id] = {
                    "id": rule_id,
                    "name": finding.title.replace(" ", ""),
                    "shortDescription": {"text": finding.title},
                    "fullDescription": {"text": finding.description or finding.title},
                    "defaultConfiguration": {
                        "level": level_map.get(finding.severity, "warning")
                    },
                    "properties": {
                        "category": finding.category,
                        "persona": finding.persona_id,
                        "severity": finding.severity.value,
                    }
                }

            line_num = max(1, finding.line_number or 1)
            result_item = {
                "ruleId": rule_id,
                "level": level_map.get(finding.severity, "warning"),
                "message": {
                    "text": f"[{finding.severity.value}] {finding.title}: {finding.recommendation}"
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": finding.file_path,
                                "uriBaseId": "%SRCROOT%",
                            },
                            "region": {
                                "startLine": line_num,
                                "startColumn": 1,
                            }
                        }
                    }
                ],
                "properties": {
                    "recommendation": finding.recommendation,
                    "category": finding.category,
                }
            }
            results.append(result_item)

        sarif_doc = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "PanelReview",
                            "version": "1.0.0",
                            "informationUri": "https://github.com/sujanv/PanelReview",
                            "rules": list(rules_map.values()),
                        }
                    },
                    "results": results,
                    "invocations": [
                        {
                            "executionSuccessful": True,
                            "endTimeUtc": report.timestamp,
                        }
                    ]
                }
            ]
        }
        return sarif_doc

    @staticmethod
    def to_sarif_json(report: ConsensusReport, indent: int = 2) -> str:
        return json.dumps(SarifExporter.to_sarif(report), indent=indent)
