"""
Core data models for PanelReview.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

    @property
    def weight(self) -> int:
        return {
            SeverityLevel.CRITICAL: 25,
            SeverityLevel.HIGH: 15,
            SeverityLevel.MEDIUM: 8,
            SeverityLevel.LOW: 3,
            SeverityLevel.INFO: 0,
        }[self]

    @property
    def badge_color(self) -> str:
        return {
            SeverityLevel.CRITICAL: "#dc2626", # Red
            SeverityLevel.HIGH: "#ea580c",     # Orange
            SeverityLevel.MEDIUM: "#ca8a04",   # Amber
            SeverityLevel.LOW: "#2563eb",      # Blue
            SeverityLevel.INFO: "#64748b",     # Slate
        }[self]


class ReviewVerdict(str, Enum):
    APPROVED = "APPROVED"
    APPROVED_WITH_CONDITIONS = "APPROVED_WITH_CONDITIONS"
    NEEDS_REVISION = "NEEDS_REVISION"
    REJECTED = "REJECTED"


@dataclass
class ReviewFinding:
    title: str
    severity: SeverityLevel
    file_path: str
    line_number: Optional[int] = None
    description: str = ""
    recommendation: str = ""
    code_snippet: Optional[str] = None
    category: str = "general"
    persona_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "description": self.description,
            "recommendation": self.recommendation,
            "code_snippet": self.code_snippet,
            "category": self.category,
            "persona_id": self.persona_id,
        }


@dataclass
class PersonaReviewResult:
    persona_id: str
    persona_name: str
    persona_title: str
    persona_emoji: str
    model_used: str
    summary: str
    score: int  # 0 to 100
    findings: List[ReviewFinding] = field(default_factory=list)
    verdict: ReviewVerdict = ReviewVerdict.APPROVED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "persona_name": self.persona_name,
            "persona_title": self.persona_title,
            "persona_emoji": self.persona_emoji,
            "model_used": self.model_used,
            "summary": self.summary,
            "score": self.score,
            "findings": [f.to_dict() for f in self.findings],
            "verdict": self.verdict.value,
        }


@dataclass
class ScannedFile:
    path: str
    relative_path: str
    language: str
    lines_count: int
    size_bytes: int
    content: str


@dataclass
class RepositoryInfo:
    source: str
    is_remote: bool
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    total_files: int = 0
    total_lines: int = 0
    languages: Dict[str, int] = field(default_factory=dict)  # language -> file count
    files: List[ScannedFile] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "is_remote": self.is_remote,
            "branch": self.branch,
            "commit_hash": self.commit_hash,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "languages": self.languages,
        }


@dataclass
class ConsensusReport:
    timestamp: str
    repository: RepositoryInfo
    overall_verdict: ReviewVerdict
    overall_score: int
    persona_results: List[PersonaReviewResult] = field(default_factory=list)
    consolidated_findings: List[ReviewFinding] = field(default_factory=list)
    executive_summary: str = ""
    action_items: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "repository": self.repository.to_dict(),
            "overall_verdict": self.overall_verdict.value,
            "overall_score": self.overall_score,
            "persona_results": [p.to_dict() for p in self.persona_results],
            "consolidated_findings": [f.to_dict() for f in self.consolidated_findings],
            "executive_summary": self.executive_summary,
            "action_items": self.action_items,
        }
