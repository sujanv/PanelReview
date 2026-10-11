"""
Report generators: Markdown, HTML Dashboard, and JSON.
"""

import json
from datetime import datetime
from panel_review.models import ConsensusReport, SeverityLevel, ReviewVerdict


class ReportGenerator:
    @staticmethod
    def to_markdown(report: ConsensusReport) -> str:
        lines = []
        verdict_badge = {
            ReviewVerdict.APPROVED: "🟢 **APPROVED**",
            ReviewVerdict.APPROVED_WITH_CONDITIONS: "🟡 **APPROVED WITH CONDITIONS**",
            ReviewVerdict.NEEDS_REVISION: "🟠 **NEEDS REVISION**",
            ReviewVerdict.REJECTED: "🔴 **REJECTED**",
        }.get(report.overall_verdict, report.overall_verdict.value)

        lines.append("# 🏛️ AI Agent Panel Review Report\n")
        lines.append(f"**Target**: `{report.repository.source}`  ")
        lines.append(f"**Generated**: `{report.timestamp}`  ")
        if report.repository.branch:
            lines.append(f"**Branch**: `{report.repository.branch}`  ")
        if report.repository.commit_hash:
            lines.append(f"**Commit**: `{report.repository.commit_hash}`  ")
        lines.append(f"**Overall Verdict**: {verdict_badge}  ")
        lines.append(f"**Overall Health Score**: **{report.overall_score}/100**\n")

        lines.append("## 📊 Repository Overview")
        lines.append(f"- **Total Files Scanned**: {report.repository.total_files}")
        lines.append(f"- **Total Lines of Code**: {report.repository.total_lines}")
        langs_str = ", ".join([f"`{k}`: {v}" for k, v in report.repository.languages.items()])
        lines.append(f"- **Languages Detected**: {langs_str or 'None'}\n")

        lines.append("## ⚖️ Executive Summary")
        lines.append(f"> {report.executive_summary}\n")

        if report.action_items:
            lines.append("## 🎯 Prioritized Action Items")
            for idx, item in enumerate(report.action_items, 1):
                lines.append(f"{idx}. {item}")
            lines.append("")

        lines.append("## 🧑‍💻 Panel Personas Summary")
        lines.append("| Persona | Model | Score | Findings | Verdict |")
        lines.append("| :--- | :--- | :---: | :---: | :--- |")
        for p in report.persona_results:
            lines.append(
                f"| {p.persona_emoji} **{p.persona_name}** | `{p.model_used}` | **{p.score}/100** | {len(p.findings)} | `{p.verdict.value}` |"
            )
        lines.append("")

        lines.append("## 🔍 Detailed Persona Evaluations")
        for p in report.persona_results:
            lines.append(f"### {p.persona_emoji} {p.persona_name} — {p.persona_title}")
            lines.append(f"*Assessment*: {p.summary}\n")
            if not p.findings:
                lines.append("✅ *No critical findings reported by this persona.*\n")
            else:
                lines.append("| Severity | Title | File / Line | Recommendation |")
                lines.append("| :--- | :--- | :--- | :--- |")
                for f in p.findings:
                    loc = f"`{f.file_path}`"
                    if f.line_number:
                        loc += f":{f.line_number}"
                    lines.append(
                        f"| **{f.severity.value}** | {f.title} | {loc} | {f.recommendation} |"
                    )
                lines.append("")

        lines.append("---\n*Generated autonomously by PanelReview AI Multi-Persona System.*")
        return "\n".join(lines)

    @staticmethod
    def to_json(report: ConsensusReport, indent: int = 2) -> str:
        return json.dumps(report.to_dict(), indent=indent)

    @staticmethod
    def to_html(report: ConsensusReport) -> str:
        verdict_color = {
            ReviewVerdict.APPROVED: "#16a34a",
            ReviewVerdict.APPROVED_WITH_CONDITIONS: "#ca8a04",
            ReviewVerdict.NEEDS_REVISION: "#ea580c",
            ReviewVerdict.REJECTED: "#dc2626",
        }.get(report.overall_verdict, "#2563eb")

        findings_rows = []
        for p in report.persona_results:
            for f in p.findings:
                color = f.severity.badge_color
                line_str = f":{f.line_number}" if f.line_number else ""
                findings_rows.append(f"""
                <tr>
                    <td><span class="badge" style="background-color: {color};">{f.severity.value}</span></td>
                    <td><strong>{f.title}</strong><br><small style="color:#64748b;">{f.category}</small></td>
                    <td><code>{f.file_path}{line_str}</code></td>
                    <td>{p.persona_emoji} {p.persona_name}</td>
                    <td>{f.recommendation}</td>
                </tr>
                """)

        personas_cards = []
        for p in report.persona_results:
            personas_cards.append(f"""
            <div class="card">
                <div class="card-header">
                    <span class="emoji">{p.persona_emoji}</span>
                    <div>
                        <div class="persona-name">{p.persona_name}</div>
                        <div class="persona-title">{p.persona_title}</div>
                    </div>
                    <div class="persona-score">{p.score}<span>/100</span></div>
                </div>
                <div class="persona-model">Model: <code>{p.model_used}</code></div>
                <p class="persona-summary">{p.summary}</p>
                <div class="card-footer">
                    <span>Findings: <strong>{len(p.findings)}</strong></span>
                    <span class="status-tag status-{p.verdict.value.lower()}">{p.verdict.value}</span>
                </div>
            </div>
            """)

        actions_html = "".join([f"<li>{item}</li>" for item in report.action_items])

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Panel Review Report - {report.repository.source}</title>
    <style>
        :root {{
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-hover: #334155;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --accent: #3b82f6;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background-color: var(--bg); color: var(--text); padding: 2rem; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 1.5rem; margin-bottom: 2rem; }}
        .header-title h1 {{ font-size: 2rem; display: flex; align-items: center; gap: 0.5rem; }}
        .header-meta {{ color: var(--text-muted); font-size: 0.9rem; margin-top: 0.5rem; }}
        .verdict-box {{ text-align: right; }}
        .verdict-tag {{ display: inline-block; padding: 0.5rem 1.2rem; border-radius: 9999px; font-weight: bold; font-size: 1.1rem; color: white; background-color: {verdict_color}; }}
        .score-circle {{ font-size: 2.5rem; font-weight: 800; color: #38bdf8; }}
        
        .section {{ margin-bottom: 2.5rem; }}
        .section-title {{ font-size: 1.4rem; border-left: 4px solid var(--accent); padding-left: 0.75rem; margin-bottom: 1rem; color: #e2e8f0; }}
        
        .executive-box {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; font-size: 1.05rem; line-height: 1.7; }}
        .action-list {{ background: var(--surface); border-radius: 12px; padding: 1.5rem 2rem; border: 1px solid var(--border); }}
        .action-list li {{ margin-bottom: 0.75rem; color: #f1f5f9; }}
        
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 1.5rem; }}
        .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; display: flex; flex-direction: column; justify-content: space-between; }}
        .card-header {{ display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }}
        .emoji {{ font-size: 2rem; }}
        .persona-name {{ font-weight: bold; font-size: 1.1rem; }}
        .persona-title {{ font-size: 0.8rem; color: var(--text-muted); }}
        .persona-score {{ margin-left: auto; font-size: 1.6rem; font-weight: bold; color: #38bdf8; }}
        .persona-score span {{ font-size: 0.9rem; color: var(--text-muted); }}
        .persona-model {{ font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.75rem; }}
        .persona-summary {{ font-size: 0.95rem; color: #cbd5e1; margin-bottom: 1rem; flex-grow: 1; }}
        .card-footer {{ display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border); padding-top: 0.75rem; font-size: 0.85rem; }}
        
        .status-tag {{ padding: 0.2rem 0.6rem; border-radius: 6px; font-weight: 600; text-transform: uppercase; font-size: 0.75rem; }}
        .status-approved {{ background: #14532d; color: #4ade80; }}
        .status-approved_with_conditions {{ background: #713f12; color: #facc15; }}
        .status-needs_revision {{ background: #7c2d12; color: #fb923c; }}
        .status-rejected {{ background: #7f1d1d; color: #f87171; }}
        
        table {{ width: 100%; border-collapse: collapse; background: var(--surface); border-radius: 12px; overflow: hidden; border: 1px solid var(--border); }}
        th, td {{ padding: 0.9rem 1rem; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.9rem; }}
        th {{ background: #172554; font-weight: 600; color: #93c5fd; }}
        tr:hover {{ background: var(--surface-hover); }}
        code {{ background: #090d16; padding: 0.2rem 0.4rem; border-radius: 4px; font-family: monospace; font-size: 0.85rem; color: #38bdf8; }}
        .badge {{ display: inline-block; padding: 0.25rem 0.5rem; border-radius: 6px; font-weight: bold; font-size: 0.75rem; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-title">
                <h1>🏛️ AI Agent Panel Review Report</h1>
                <div class="header-meta">
                    Target: <code>{report.repository.source}</code> &bull; Generated: {report.timestamp} &bull; Files: {report.repository.total_files} ({report.repository.total_lines} LOC)
                </div>
            </div>
            <div class="verdict-box">
                <div class="score-circle">{report.overall_score}/100</div>
                <div class="verdict-tag">{report.overall_verdict.value.replace('_', ' ')}</div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">⚖️ Executive Consensus</h2>
            <div class="executive-box">
                {report.executive_summary}
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">🎯 Prioritized Action Items</h2>
            <ol class="action-list">
                {actions_html}
            </ol>
        </div>

        <div class="section">
            <h2 class="section-title">🧑‍💻 Panel Personas Evaluation</h2>
            <div class="grid">
                {"".join(personas_cards)}
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">🔍 Consolidated Findings ({len(report.consolidated_findings)})</h2>
            <table>
                <thead>
                    <tr>
                        <th>Severity</th>
                        <th>Finding & Category</th>
                        <th>File Location</th>
                        <th>Persona</th>
                        <th>Actionable Recommendation</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(findings_rows) if findings_rows else '<tr><td colspan="5" style="text-align:center;">No issues identified!</td></tr>'}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
        """
        return html
