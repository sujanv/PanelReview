"""
Automated Remediation and Patch Generator.
Generates code fixes and unified diffs (.patch) for identified panel review findings.
"""

import os
import difflib
from dataclasses import dataclass
from typing import List, Optional, Dict
from panel_review.models import ReviewFinding, ConsensusReport


@dataclass
class CodePatch:
    finding_title: str
    file_path: str
    original_snippet: str
    remediated_snippet: str
    unified_diff: str
    line_number: Optional[int] = None


class PatchRemediator:
    @staticmethod
    def generate_patch_for_finding(finding: ReviewFinding, file_content: str) -> Optional[CodePatch]:
        """
        Synthesizes a proposed code fix and unified diff for an identified finding.
        """
        lines = file_content.splitlines(keepends=True)
        if not lines:
            return None

        target_line = max(1, min(len(lines), finding.line_number or 1)) - 1
        original_line = lines[target_line]

        # Heuristic fix strategies based on finding category
        fixed_line = original_line
        cat_lower = (finding.category or "").lower()
        title_lower = finding.title.lower()

        if "timeout" in title_lower or "timeout" in cat_lower:
            if "http" in original_line.lower() or "get(" in original_line or "post(" in original_line:
                if "timeout" not in original_line:
                    fixed_line = original_line.rstrip() + ", timeout=10.0)\n" if ")" in original_line else original_line
        elif "hardcoded" in title_lower or "credentials" in title_lower:
            if "=" in original_line and ("key" in original_line.lower() or "secret" in original_line.lower() or "password" in original_line.lower()):
                var_name = original_line.split("=")[0].strip()
                fixed_line = f"{var_name} = os.getenv('{var_name.upper()}', '')\n"
        elif "trace" in title_lower or "telemetry" in cat_lower:
            if "logger." in original_line:
                fixed_line = original_line.replace('logger.info(', 'logger.info("[trace_id=%s] " % get_current_trace_id(), ')

        if fixed_line == original_line:
            # Add an inline TODO annotation recommendation
            fixed_line = f"# TODO [PanelReview {finding.persona_id}]: {finding.recommendation}\n" + original_line

        modified_lines = list(lines)
        modified_lines[target_line] = fixed_line

        diff = "".join(difflib.unified_diff(
            lines,
            modified_lines,
            fromfile=f"a/{finding.file_path}",
            tofile=f"b/{finding.file_path}",
            lineterm="",
        ))

        return CodePatch(
            finding_title=finding.title,
            file_path=finding.file_path,
            original_snippet=original_line.strip(),
            remediated_snippet=fixed_line.strip(),
            unified_diff=diff,
            line_number=target_line + 1,
        )

    @staticmethod
    def generate_all_patches(report: ConsensusReport, base_dir: str = ".") -> List[CodePatch]:
        """
        Generates patches for all actionable findings in a ConsensusReport.
        """
        patches: List[CodePatch] = []
        for finding in report.consolidated_findings:
            full_path = os.path.join(base_dir, finding.file_path)
            if os.path.isfile(full_path):
                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    patch = PatchRemediator.generate_patch_for_finding(finding, content)
                    if patch and patch.unified_diff:
                        patches.append(patch)
                except Exception:
                    pass
        return patches

    @staticmethod
    def export_unified_patch_file(patches: List[CodePatch], output_path: str = "panel_review_fixes.patch") -> str:
        """
        Exports all patches into a standard git-applyable unified patch file.
        """
        diff_text = "\n\n".join([p.unified_diff for p in patches if p.unified_diff])
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(diff_text)
        return output_path
