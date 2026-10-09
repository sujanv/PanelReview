"""
Repository scanner for local files and project trees.
"""

import os
import fnmatch
from typing import List, Dict, Optional, Set
from panel_review.config import ScannerConfig
from panel_review.models import ScannedFile, RepositoryInfo
from panel_review.scanner.language_detect import detect_language


class RepoScanner:
    def __init__(self, config: Optional[ScannerConfig] = None):
        self.config = config or ScannerConfig()

    def scan_directory(self, root_path: str, max_files: Optional[int] = None) -> RepositoryInfo:
        abs_root = os.path.abspath(root_path)
        if not os.path.exists(abs_root):
            raise FileNotFoundError(f"Path does not exist: {abs_root}")

        if os.path.isfile(abs_root):
            # Single file review
            scanned = self._scan_single_file(abs_root, os.path.dirname(abs_root))
            files = [scanned] if scanned else []
            langs = {files[0].language: 1} if files else {}
            total_lines = files[0].lines_count if files else 0
            return RepositoryInfo(
                source=abs_root,
                is_remote=False,
                total_files=len(files),
                total_lines=total_lines,
                languages=langs,
                files=files,
            )

        limit = max_files or self.config.max_total_files
        gitignore_patterns = self._load_gitignore(abs_root) if self.config.respect_gitignore else []

        scanned_files: List[ScannedFile] = []
        lang_counts: Dict[str, int] = {}
        total_lines = 0

        for current_root, dirs, filenames in os.walk(abs_root):
            # Exclude directories
            dirs[:] = [
                d for d in dirs
                if not self._is_excluded_dir(d, current_root, abs_root, gitignore_patterns)
            ]

            for filename in sorted(filenames):
                if len(scanned_files) >= limit:
                    break

                full_path = os.path.join(current_root, filename)
                rel_path = os.path.relpath(full_path, abs_root)

                if self._is_excluded_file(filename, rel_path, gitignore_patterns):
                    continue

                scanned = self._scan_single_file(full_path, abs_root)
                if scanned:
                    scanned_files.append(scanned)
                    lang_counts[scanned.language] = lang_counts.get(scanned.language, 0) + 1
                    total_lines += scanned.lines_count

            if len(scanned_files) >= limit:
                break

        return RepositoryInfo(
            source=abs_root,
            is_remote=False,
            total_files=len(scanned_files),
            total_lines=total_lines,
            languages=lang_counts,
            files=scanned_files,
        )

    def _scan_single_file(self, full_path: str, root_dir: str) -> Optional[ScannedFile]:
        try:
            size = os.path.getsize(full_path)
            max_bytes = self.config.max_file_size_kb * 1024
            if size > max_bytes:
                return None

            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            first_line = content.splitlines()[0] if content else ""
            language = detect_language(full_path, first_line)
            lines_count = len(content.splitlines())
            rel_path = os.path.relpath(full_path, root_dir)

            return ScannedFile(
                path=full_path,
                relative_path=rel_path,
                language=language,
                lines_count=lines_count,
                size_bytes=size,
                content=content,
            )
        except Exception:
            return None

    def _load_gitignore(self, root_path: str) -> List[str]:
        patterns = []
        git_ignore_path = os.path.join(root_path, ".gitignore")
        if os.path.exists(git_ignore_path):
            try:
                with open(git_ignore_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            patterns.append(line)
            except Exception:
                pass
        return patterns

    def _is_excluded_dir(self, dir_name: str, current_dir: str, root_dir: str, gitignore_patterns: List[str]) -> bool:
        if dir_name in self.config.exclude_dirs:
            return True
        if dir_name.startswith("."):
            return True
        rel = os.path.relpath(os.path.join(current_dir, dir_name), root_dir)
        for pat in gitignore_patterns:
            pat_clean = pat.rstrip("/")
            if fnmatch.fnmatch(dir_name, pat_clean) or fnmatch.fnmatch(rel, pat_clean):
                return True
        return False

    def _is_excluded_file(self, filename: str, rel_path: str, gitignore_patterns: List[str]) -> bool:
        for pat in self.config.exclude_files:
            if fnmatch.fnmatch(filename, pat) or fnmatch.fnmatch(rel_path, pat):
                return True
        for pat in gitignore_patterns:
            if fnmatch.fnmatch(filename, pat) or fnmatch.fnmatch(rel_path, pat):
                return True
        return False
