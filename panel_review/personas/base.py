"""
Base class for Panel Review Personas.
"""

import json
import re
from abc import ABC
from typing import List, Optional, Dict, Any
from panel_review.models import (
    ReviewFinding,
    PersonaReviewResult,
    SeverityLevel,
    ReviewVerdict,
    ScannedFile,
    RepositoryInfo,
)


class Persona(ABC):
    def __init__(
        self,
        persona_id: str,
        name: str,
        title: str,
        emoji: str = "🧑‍💻",
        focus_areas: Optional[List[str]] = None,
        severity_threshold: str = "LOW",
        custom_system_prompt: Optional[str] = None,
    ):
        self.persona_id = persona_id
        self.name = name
        self.title = title
        self.emoji = emoji
        self.focus_areas = focus_areas or []
        self.severity_threshold = severity_threshold.upper()
        self.custom_system_prompt = custom_system_prompt

    def build_system_prompt(self) -> str:
        if self.custom_system_prompt:
            return self.custom_system_prompt

        focus_list = "\n".join([f"- {area}" for area in self.focus_areas])
        return (
            f"You are the {self.name} ({self.title}) participating in an expert AI Panel Review.\n"
            f"Your specific domain areas of responsibility are:\n{focus_list}\n\n"
            "Review the provided polyglot source code strictly from your specialized persona's perspective.\n"
            "Output your findings in valid JSON adhering to the following structure:\n"
            "{\n"
            '  "summary": "2-3 sentences summarizing your expert domain assessment.",\n'
            '  "score": 85, // integer 0-100 (100 being flawless)\n'
            '  "findings": [\n'
            "    {\n"
            '      "title": "Concise issue summary",\n'
            '      "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",\n'
            '      "file_path": "path/to/file.ext",\n'
            '      "line_number": 42,\n'
            '      "description": "Clear explanation of the risk or anti-pattern",\n'
            '      "recommendation": "Concrete, actionable code fix or mitigation",\n'
            '      "category": "CWE / OWASP / SRE / Performance domain category"\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "Ensure you return ONLY valid JSON (enclosed in ```json ... ``` or directly)."
        )

    def build_review_prompt(self, files: List[ScannedFile], repo_info: RepositoryInfo) -> str:
        prompt_parts = [
            f"# Repository Review Target: {repo_info.source}",
            f"Total Files: {repo_info.total_files} | Total Lines: {repo_info.total_lines}",
            f"Languages: {', '.join([f'{k}: {v}' for k, v in repo_info.languages.items()])}",
            "\n## Files to inspect:\n"
        ]

        for file in files:
            prompt_parts.append(
                f"--- BEGIN FILE: {file.relative_path} ({file.language}, {file.lines_count} lines) ---\n"
                f"{file.content}\n"
                f"--- END FILE: {file.relative_path} ---\n"
            )

        prompt_parts.append(
            f"\nAs the {self.name}, review these files according to your focus areas.\n"
            "Provide your structured JSON review now:"
        )

        return "\n".join(prompt_parts)

    def parse_llm_response(self, response_text: str, model_used: str = "unknown") -> PersonaReviewResult:
        """
        Parses LLM JSON response and builds PersonaReviewResult.
        """
        cleaned = response_text.strip()
        # Extract markdown code block if present
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if json_match:
            cleaned = json_match.group(1).strip()

        try:
            data = json.loads(cleaned)
        except Exception:
            # Fallback regex extraction if JSON decoding fails
            data = {
                "summary": cleaned[:300],
                "score": 75,
                "findings": []
            }

        summary = data.get("summary", "Review complete.")
        score = int(data.get("score", 75))
        raw_findings = data.get("findings", [])

        findings: List[ReviewFinding] = []
        has_critical = False
        has_high = False

        for rf in raw_findings:
            if not isinstance(rf, dict):
                continue
            sev_str = str(rf.get("severity", "LOW")).upper()
            try:
                sev = SeverityLevel(sev_str)
            except ValueError:
                sev = SeverityLevel.LOW

            if sev == SeverityLevel.CRITICAL:
                has_critical = True
            elif sev == SeverityLevel.HIGH:
                has_high = True

            findings.append(ReviewFinding(
                title=rf.get("title", "Unspecified Finding"),
                severity=sev,
                file_path=rf.get("file_path", "unknown"),
                line_number=rf.get("line_number"),
                description=rf.get("description", ""),
                recommendation=rf.get("recommendation", ""),
                code_snippet=rf.get("code_snippet"),
                category=rf.get("category", self.persona_id),
                persona_id=self.persona_id,
            ))

        # Determine verdict
        if has_critical or score < 50:
            verdict = ReviewVerdict.REJECTED
        elif has_high or score < 75:
            verdict = ReviewVerdict.NEEDS_REVISION
        elif score < 90:
            verdict = ReviewVerdict.APPROVED_WITH_CONDITIONS
        else:
            verdict = ReviewVerdict.APPROVED

        return PersonaReviewResult(
            persona_id=self.persona_id,
            persona_name=self.name,
            persona_title=self.title,
            persona_emoji=self.emoji,
            model_used=model_used,
            summary=summary,
            score=score,
            findings=findings,
            verdict=verdict,
        )
