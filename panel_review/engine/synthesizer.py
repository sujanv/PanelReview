"""
Synthesizer helpers for consensus scoring and finding deduplication.
"""

from typing import List, Dict
from panel_review.models import ReviewFinding, SeverityLevel


class ReviewSynthesizer:
    @staticmethod
    def deduplicate_findings(findings: List[ReviewFinding]) -> List[ReviewFinding]:
        """
        Deduplicates similar findings across personas based on file_path, line_number, and title similarity.
        """
        seen: Dict[str, ReviewFinding] = {}
        for f in findings:
            key = f"{f.file_path}:{f.line_number or 0}:{f.title.lower().strip()}"
            if key not in seen:
                seen[key] = f
            else:
                # Keep the one with higher severity
                if f.severity.weight > seen[key].severity.weight:
                    seen[key] = f
        return list(seen.values())

    @staticmethod
    def calculate_health_score(findings: List[ReviewFinding], base_score: int = 100) -> int:
        penalty = 0
        for f in findings:
            penalty += f.severity.weight
        return max(0, min(100, base_score - penalty))
