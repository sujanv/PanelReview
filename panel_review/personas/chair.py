"""
Panel Review Chair for consensus synthesis and executive decision making.
"""

import json
import re
from typing import List, Dict, Any, Optional
from panel_review.models import (
    PersonaReviewResult,
    ConsensusReport,
    ReviewVerdict,
    ReviewFinding,
    RepositoryInfo,
    SeverityLevel,
)
from datetime import datetime


class PanelChair:
    def __init__(
        self,
        chair_title: str = "Panel Review Chair",
        chair_emoji: str = "⚖️",
        min_approval_score: int = 75,
        critical_issues_block_approval: bool = True,
    ):
        self.chair_title = chair_title
        self.chair_emoji = chair_emoji
        self.min_approval_score = min_approval_score
        self.critical_issues_block_approval = critical_issues_block_approval

    def build_consensus_prompt(
        self,
        repo_info: RepositoryInfo,
        persona_results: List[PersonaReviewResult],
    ) -> str:
        prompt_parts = [
            f"# Panel Review Synthesis for: {repo_info.source}",
            f"Repository Stats: {repo_info.total_files} files, {repo_info.total_lines} lines of code.",
            f"Languages: {', '.join([f'{k}: {v}' for k, v in repo_info.languages.items()])}",
            "\n## Specialist Persona Evaluations:\n"
        ]

        for p in persona_results:
            prompt_parts.append(
                f"### {p.persona_emoji} {p.persona_name} ({p.persona_title})\n"
                f"- Model: {p.model_used}\n"
                f"- Score: {p.score}/100 | Verdict: {p.verdict.value}\n"
                f"- Summary: {p.summary}\n"
                f"- Findings Count: {len(p.findings)}\n"
            )
            for f in p.findings:
                prompt_parts.append(
                    f"  * [{f.severity.value}] {f.title} ({f.file_path}:{f.line_number or 1}) - {f.description}"
                )
            prompt_parts.append("")

        prompt_parts.append(
            "Synthesize all findings as the Panel Chair.\n"
            "Produce a final JSON consensus report with:\n"
            "{\n"
            '  "executive_summary": "Comprehensive 3-5 sentence executive verdict summarising strengths and risks.",\n'
            '  "overall_score": 85, // calibrated score 0-100\n'
            '  "verdict": "APPROVED|APPROVED_WITH_CONDITIONS|NEEDS_REVISION|REJECTED",\n'
            '  "action_items": [\n'
            '    "Prioritized concrete next step 1",\n'
            '    "Prioritized concrete next step 2"\n'
            '  ]\n'
            "}\n"
            "Respond ONLY with valid JSON."
        )

        return "\n".join(prompt_parts)

    def synthesize(
        self,
        repo_info: RepositoryInfo,
        persona_results: List[PersonaReviewResult],
        llm_synthesis_text: Optional[str] = None,
    ) -> ConsensusReport:
        # Collect all findings
        all_findings: List[ReviewFinding] = []
        critical_count = 0
        high_count = 0

        for pres in persona_results:
            for f in pres.findings:
                all_findings.append(f)
                if f.severity == SeverityLevel.CRITICAL:
                    critical_count += 1
                elif f.severity == SeverityLevel.HIGH:
                    high_count += 1

        # Calculate average persona score
        if persona_results:
            avg_score = int(sum(p.score for p in persona_results) / len(persona_results))
        else:
            avg_score = 100

        executive_summary = ""
        action_items: List[str] = []
        overall_score = avg_score
        verdict = ReviewVerdict.APPROVED

        if llm_synthesis_text:
            cleaned = llm_synthesis_text.strip()
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if json_match:
                cleaned = json_match.group(1).strip()
            try:
                data = json.loads(cleaned)
                executive_summary = data.get("executive_summary", "")
                overall_score = int(data.get("overall_score", avg_score))
                action_items = data.get("action_items", [])
                v_str = str(data.get("verdict", "")).upper()
                if v_str in ReviewVerdict.__members__:
                    verdict = ReviewVerdict[v_str]
            except Exception:
                pass

        if not executive_summary:
            executive_summary = (
                f"The AI Panel Review convened across {len(persona_results)} specialist personas. "
                f"Total findings recorded: {len(all_findings)} (Critical: {critical_count}, High: {high_count}). "
                f"Overall repository health score is {overall_score}/100."
            )

        # Enforce chair policies
        if self.critical_issues_block_approval and critical_count > 0:
            verdict = ReviewVerdict.REJECTED
        elif high_count > 0 or overall_score < self.min_approval_score:
            if verdict not in (ReviewVerdict.REJECTED, ReviewVerdict.NEEDS_REVISION):
                verdict = ReviewVerdict.NEEDS_REVISION
        elif overall_score < 90 and verdict == ReviewVerdict.APPROVED:
            verdict = ReviewVerdict.APPROVED_WITH_CONDITIONS

        if not action_items:
            # Generate default prioritized actions from findings
            sorted_findings = sorted(all_findings, key=lambda x: x.severity.weight, reverse=True)
            for f in sorted_findings[:5]:
                action_items.append(f"[{f.severity.value}] {f.title} ({f.file_path}) - {f.recommendation}")

        return ConsensusReport(
            timestamp=datetime.utcnow().isoformat() + "Z",
            repository=repo_info,
            overall_verdict=verdict,
            overall_score=overall_score,
            persona_results=persona_results,
            consolidated_findings=all_findings,
            executive_summary=executive_summary,
            action_items=action_items,
        )
