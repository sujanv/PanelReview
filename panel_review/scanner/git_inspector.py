"""
Git repository inspector, cloning, and diff analysis.
"""

import os
import shutil
import tempfile
import subprocess
from typing import Optional, Tuple, List
from panel_review.models import RepositoryInfo, ScannedFile
from panel_review.scanner.repo_scanner import RepoScanner
from panel_review.config import ScannerConfig
from panel_review.scanner.language_detect import detect_language


class GitInspector:
    def __init__(self, scanner_config: Optional[ScannerConfig] = None):
        self.scanner_config = scanner_config or ScannerConfig()
        self.repo_scanner = RepoScanner(self.scanner_config)

    def is_git_repo(self, path: str) -> bool:
        return os.path.exists(os.path.join(path, ".git"))

    def get_git_info(self, path: str) -> Tuple[Optional[str], Optional[str]]:
        """Returns (branch_name, commit_hash) for a git directory."""
        if not self.is_git_repo(path):
            return None, None
        branch = None
        commit = None
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=path, capture_output=True, text=True, check=True
            )
            branch = res.stdout.strip()
        except Exception:
            pass

        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=path, capture_output=True, text=True, check=True
            )
            commit = res.stdout.strip()[:8]
        except Exception:
            pass

        return branch, commit

    def inspect_diff(self, path: str, target_ref: str = "HEAD") -> RepositoryInfo:
        """
        Gathers changed files from git diff (staged + unstaged, or against ref).
        """
        abs_path = os.path.abspath(path)
        branch, commit = self.get_git_info(abs_path)

        # Get changed file names
        cmd = ["git", "diff", "--name-only", target_ref]
        res = subprocess.run(cmd, cwd=abs_path, capture_output=True, text=True)
        changed_paths = [p.strip() for p in res.stdout.splitlines() if p.strip()]

        # Also include untracked files
        cmd_untracked = ["git", "status", "--porcelain"]
        res_u = subprocess.run(cmd_untracked, cwd=abs_path, capture_output=True, text=True)
        for line in res_u.stdout.splitlines():
            if line.startswith("?? "):
                changed_paths.append(line[3:].strip())

        changed_paths = sorted(list(set(changed_paths)))

        scanned_files: List[ScannedFile] = []
        lang_counts = {}
        total_lines = 0

        for rel_path in changed_paths:
            full_path = os.path.join(abs_path, rel_path)
            if not os.path.isfile(full_path):
                continue
            scanned = self.repo_scanner._scan_single_file(full_path, abs_path)
            if scanned:
                scanned_files.append(scanned)
                lang_counts[scanned.language] = lang_counts.get(scanned.language, 0) + 1
                total_lines += scanned.lines_count

        return RepositoryInfo(
            source=f"{abs_path} (git diff against {target_ref})",
            is_remote=False,
            branch=branch,
            commit_hash=commit,
            total_files=len(scanned_files),
            total_lines=total_lines,
            languages=lang_counts,
            files=scanned_files,
        )

    def clone_remote(
        self,
        git_url: str,
        branch: Optional[str] = None,
        depth: int = 1,
    ) -> Tuple[RepositoryInfo, str]:
        """
        Clones a remote git repository into a temporary directory and scans it.
        Returns (RepositoryInfo, temp_dir_path). Caller is responsible for cleaning temp_dir_path if desired.
        """
        temp_dir = tempfile.mkdtemp(prefix="panel_review_clone_")
        clone_cmd = ["git", "clone", "--depth", str(depth)]
        if branch:
            clone_cmd.extend(["--branch", branch])
        clone_cmd.extend([git_url, temp_dir])

        try:
            subprocess.run(clone_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to clone remote repository {git_url}: {e.stderr}") from e

        branch_name, commit_hash = self.get_git_info(temp_dir)
        repo_info = self.repo_scanner.scan_directory(temp_dir)
        repo_info.source = git_url
        repo_info.is_remote = True
        repo_info.branch = branch_name
        repo_info.commit_hash = commit_hash

        return repo_info, temp_dir
