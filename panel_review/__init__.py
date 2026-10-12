"""
PanelReview: AI-based Multi-Persona Agent Panel Review System.
"""

__version__ = "1.0.0"
__author__ = "PanelReview Team"

from panel_review.models import (
    SeverityLevel,
    ReviewFinding,
    PersonaReviewResult,
    ConsensusReport,
    ScannedFile,
    RepositoryInfo,
)
from panel_review.config import PanelConfig, load_config
from panel_review.engine.reviewer import ReviewEngine
from panel_review.scanner.repo_scanner import RepoScanner

__all__ = [
    "SeverityLevel",
    "ReviewFinding",
    "PersonaReviewResult",
    "ConsensusReport",
    "ScannedFile",
    "RepositoryInfo",
    "PanelConfig",
    "load_config",
    "ReviewEngine",
    "RepoScanner",
]
