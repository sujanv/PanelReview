"""
Pull Request Bot & Comment Formatter.
Generates interactive GitHub and GitLab PR review comments with collapsible cards, action item checklists, and inline diff suggestions.
"""

from typing import List, Optional
from panel_review.models import ConsensusReport, ReviewVerdict, SeverityLevel


class PRCommentGenerator:
    @staticmethod
    def format_pr_comment(report: ConsensusReport) -> str:
        verdict_badge = {
            ReviewVerdict.APPROVED: "![Approved](https://img.shields.io/badge/Panel_Review-APPROVED-success?style=flat-square)",
            ReviewVerdict.APPROVED_WITH_CONDITIONS: "![Approved with Conditions](https://img.shields.io/badge/Panel_Review-CONDITIONAL-yellow?style=flat-square)",
            ReviewVerdict.NEEDS_REVISION: "![Needs Revision](https://img.shields.io/badge/Panel_Review-NEEDS_REVISION-orange?style=flat-square)",
            ReviewVerdict.REJECTED: "![Rejected](https://img.shields.io/badge/Panel_Review-REJECTED-critical?style=flat-square)",
        }.get(report.overall_verdict, f"**{report.overall_verdict.value}**")

        lines = [
            f"## 🏛️ AI Panel Review Summary",
            f"{verdict_badge} &nbsp;&bull;&nbsp; **Overall Score**: `{report.overall_score}/100`\n",
            f"> {report.executive_summary}\n",
        ]

        # Prioritized Checklists
        if report.action_items:
            lines.append("### 🎯 Required Action Items")
            for item in report.action_items:
                lines.append(f"- [ ] {item}")
            lines.append("")

        # Persona Breakdown Table
        lines.append("### 🧑‍💻 Persona Evaluations")
        lines.append("| Persona | Model | Score | Status |")
        lines.append("| :--- | :--- | :---: | :--- |")
        for p in report.persona_results:
            lines.append(
                f"| {p.persona_emoji} **{p.persona_name}** | `{p.model_used}` | **{p.score}/100** | `{p.verdict.value}` |"
            )
        lines.append("")

        # Collapsible Detailed Persona Cards
        for p in report.persona_results:
            lines.append(f"<details><summary>{p.persona_emoji} <strong>{p.persona_name} Findings ({len(p.findings)})</strong></summary>\n")
            lines.append(f"*{p.persona_title}*\n")
            lines.append(f"> {p.summary}\n")

            if p.findings:
                for f in p.findings:
                    line_str = f":{f.line_number}" if f.line_number else ""
                    lines.append(f"#### [{f.severity.value}] {f.title} (`{f.file_path}{line_str}`)")
                    lines.append(f"- **Risk**: {f.description}")
                    lines.append(f"- **Recommendation**: {f.recommendation}\n")
            else:
                lines.append("✅ No issues reported by this persona.\n")

            lines.append("</details>\n")

        lines.append("---")
        lines.append("*Report generated autonomously by [PanelReview](https://github.com/sujanv/PanelReview).*")
        return "\n".join(lines)
