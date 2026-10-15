"""
Historical Trend and Regression Tracker.
Maintains review score progression over commits and alerts on quality/security regressions.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from panel_review.models import ConsensusReport, SeverityLevel


HISTORY_FILE = ".panel_review_history.json"


class TrendTracker:
    @staticmethod
    def record_run(report: ConsensusReport, history_file: str = HISTORY_FILE) -> Dict[str, Any]:
        """
        Records a ConsensusReport snapshot to the history file and returns regression analysis.
        """
        history = TrendTracker.load_history(history_file)

        finding_counts = {
            "CRITICAL": sum(1 for f in report.consolidated_findings if f.severity == SeverityLevel.CRITICAL),
            "HIGH": sum(1 for f in report.consolidated_findings if f.severity == SeverityLevel.HIGH),
            "MEDIUM": sum(1 for f in report.consolidated_findings if f.severity == SeverityLevel.MEDIUM),
            "LOW": sum(1 for f in report.consolidated_findings if f.severity == SeverityLevel.LOW),
        }

        persona_scores = {p.persona_id: p.score for p in report.persona_results}

        snapshot = {
            "timestamp": report.timestamp,
            "commit_hash": report.repository.commit_hash or "local",
            "branch": report.repository.branch or "main",
            "overall_score": report.overall_score,
            "overall_verdict": report.overall_verdict.value,
            "total_findings": len(report.consolidated_findings),
            "finding_counts": finding_counts,
            "persona_scores": persona_scores,
        }

        # Compare with previous run if available
        comparison = {}
        if history:
            prev = history[-1]
            score_diff = snapshot["overall_score"] - prev["overall_score"]
            crit_diff = finding_counts["CRITICAL"] - prev["finding_counts"].get("CRITICAL", 0)
            high_diff = finding_counts["HIGH"] - prev["finding_counts"].get("HIGH", 0)

            is_regression = score_diff < -5 or crit_diff > 0 or high_diff > 0
            comparison = {
                "score_delta": score_diff,
                "critical_delta": crit_diff,
                "high_delta": high_diff,
                "is_regression": is_regression,
                "previous_score": prev["overall_score"],
                "previous_commit": prev["commit_hash"],
            }

        history.append(snapshot)
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass

        return {
            "current": snapshot,
            "comparison": comparison,
            "total_runs_recorded": len(history),
        }

    @staticmethod
    def load_history(history_file: str = HISTORY_FILE) -> List[Dict[str, Any]]:
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    @staticmethod
    def format_trend_summary(analysis: Dict[str, Any]) -> str:
        curr = analysis["current"]
        comp = analysis.get("comparison", {})
        lines = ["\n📈 Panel Review Historical Trends:"]

        if not comp:
            lines.append(f"  * Baseline established! Score: {curr['overall_score']}/100 ({curr['overall_verdict']})")
        else:
            delta_str = f"+{comp['score_delta']}" if comp['score_delta'] >= 0 else str(comp['score_delta'])
            lines.append(f"  * Score Progression: {comp['previous_score']} -> {curr['overall_score']} ({delta_str} pts)")
            if comp["is_regression"]:
                lines.append("  * ⚠️ REGRESSION WARNING: Codebase health score dropped or new critical findings were introduced!")
            else:
                lines.append("  * 🟢 Progression Healthy: No regressions detected vs previous review.")

        return "\n".join(lines)
