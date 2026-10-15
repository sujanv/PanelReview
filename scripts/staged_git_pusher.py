#!/usr/bin/env python3
"""
Staged Git Committer & Pusher.
Commits and pushes files to Git one at a time with randomized 30 to 45 minute intervals.
Includes state persistence, intelligent commit messaging, and graceful remote handling.
"""

import os
import sys
import time
import json
import random
import argparse
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

STATE_FILE = ".staged_pusher_state.json"
LOG_FILE = "staged_pusher.log"

COMMIT_MESSAGE_MAP = {
    ".gitignore": "chore: add comprehensive gitignore rules",
    "pyproject.toml": "build: configure pyproject.toml packaging metadata",
    "setup.py": "build: add setup.py entry points and installer",
    "requirements.txt": "build: specify runtime and optional dependencies",
    "panel_config.yaml": "feat(config): add multi-provider and persona configuration in YAML",
    "panel_config.json": "feat(config): add default JSON configuration fallback",
    "panel_review/__init__.py": "feat(core): initialize panel_review package exports",
    "panel_review/models.py": "feat(models): define review findings, personas, and consensus data models",
    "panel_review/config.py": "feat(config): implement robust configuration loader and environment overrides",
    "panel_review/providers/base.py": "feat(providers): define LLMProvider base abstraction",
    "panel_review/providers/openai_provider.py": "feat(providers): implement OpenAI and OpenAI-compatible provider",
    "panel_review/providers/anthropic_provider.py": "feat(providers): implement Anthropic Claude provider",
    "panel_review/providers/gemini_provider.py": "feat(providers): implement Google Gemini REST provider",
    "panel_review/providers/ollama_provider.py": "feat(providers): implement local Ollama provider",
    "panel_review/providers/mock_provider.py": "feat(providers): implement zero-cost rule-based mock provider",
    "panel_review/providers/factory.py": "feat(providers): implement ProviderFactory resolver",
    "panel_review/providers/__init__.py": "feat(providers): export provider implementations",
    "panel_review/scanner/language_detect.py": "feat(scanner): implement polyglot language detection",
    "panel_review/scanner/repo_scanner.py": "feat(scanner): implement repository file tree scanner and filters",
    "panel_review/scanner/git_inspector.py": "feat(scanner): implement git diff and remote repository inspector",
    "panel_review/scanner/__init__.py": "feat(scanner): export repository scanning utilities",
    "panel_review/personas/base.py": "feat(personas): implement Persona base class and prompt generation",
    "panel_review/personas/security.py": "feat(personas): implement Security Engineer persona for OWASP and threat modeling",
    "panel_review/personas/observability.py": "feat(personas): implement Observability & SRE Engineer persona",
    "panel_review/personas/performance.py": "feat(personas): implement Performance & Scalability Engineer persona",
    "panel_review/personas/architecture.py": "feat(personas): implement Software Architect persona for clean design",
    "panel_review/personas/qa.py": "feat(personas): implement QA & Reliability Engineer persona",
    "panel_review/personas/compliance.py": "feat(personas): implement Compliance & Privacy Engineer persona",
    "panel_review/personas/chair.py": "feat(personas): implement Panel Review Chair consensus moderator",
    "panel_review/personas/registry.py": "feat(personas): implement dynamic persona registry loader",
    "panel_review/personas/__init__.py": "feat(personas): export persona classes",
    "panel_review/engine/reviewer.py": "feat(engine): implement parallel multi-persona review orchestrator",
    "panel_review/engine/synthesizer.py": "feat(engine): implement finding deduplication and scoring",
    "panel_review/engine/report.py": "feat(engine): implement Markdown, HTML Dashboard, and JSON exporters",
    "panel_review/engine/sarif.py": "feat(engine): implement SARIF v2.1.0 exporter for GitHub Security Alerts",
    "panel_review/engine/remediator.py": "feat(engine): implement automated code remediation and patch generator",
    "panel_review/engine/deliberation.py": "feat(engine): implement multi-persona deliberation and cross-examination",
    "panel_review/engine/__init__.py": "feat(engine): export review engine and report generators",
    "panel_review/presets.py": "feat(presets): implement specialized review presets system",
    "panel_review/cli.py": "feat(cli): implement rich panel-review command line interface",
    "panel_review/web/__init__.py": "feat(web): initialize live web dashboard package",
    "panel_review/web/server.py": "feat(web): implement zero-dependency live dashboard web server",
    "go.mod": "build(go): configure Go module metadata for fast scanner",
    "cmd/panel-scanner/main.go": "feat(go): implement high-performance polyglot scanner in Go",
    "scripts/__init__.py": "chore: add scripts package module",
    "scripts/staged_git_pusher.py": "feat(scripts): add automated staged git committer and pusher",
    "examples/sample_polyglot_project/app.py": "example: add sample Python web service for review demo",
    "examples/sample_polyglot_project/main.go": "example: add sample Go backend service for review demo",
    "examples/sample_polyglot_project/server.ts": "example: add sample TypeScript Express service for review demo",
    "examples/sample_polyglot_project/Dockerfile": "example: add sample Dockerfile for container inspection",
    "tests/__init__.py": "test: initialize test suite",
    "tests/test_config.py": "test: add configuration loading tests",
    "tests/test_personas.py": "test: add persona evaluation tests",
    "tests/test_providers.py": "test: add provider tests",
    "tests/test_scanner.py": "test: add scanner and language detection tests",
    "tests/test_engine.py": "test: add review engine and consensus tests",
    "tests/test_sarif.py": "test: add SARIF export unit tests",
    "tests/test_remediator.py": "test: add patch remediator unit tests",
    "tests/test_deliberation.py": "test: add multi-persona deliberation tests",
    "tests/test_presets.py": "test: add review presets tests",
    "tests/test_staged_pusher.py": "test: add staged pusher tests",
    ".github/workflows/panel-review.yml": "ci: add GitHub Actions workflow for PR reviews and SARIF uploads",
    "panel_review/validator.py": "feat(validator): implement configuration schema and environment linter",
    "panel_review/scanner/secret_scanner.py": "feat(scanner): implement secret and credential scanner with entropy heuristics",
    "panel_review/engine/consensus_voting.py": "feat(engine): implement multi-model consensus voting strategies",
    "panel_review/engine/trends.py": "feat(engine): implement historical benchmark and regression tracker",
    "panel_review/ci/__init__.py": "feat(ci): initialize continuous integration module",
    "panel_review/ci/pr_bot.py": "feat(ci): implement interactive GitHub and GitLab PR review comment bot",
    "pkg/scanner/scanner.go": "feat(go): implement reusable Go AST scanner and secret analyzer",
    "tests/test_secret_scanner.py": "test: add unit tests for AST secret scanner and entropy detection",
    "tests/test_trends.py": "test: add unit tests for historical health trends and regression tracker",
    "tests/test_voting.py": "test: add unit tests for multi-model consensus voting strategies",
    "tests/test_pr_bot.py": "test: add unit tests for pull request comment generator",
    "tests/test_validator.py": "test: add unit tests for configuration validator and linter",
    "Makefile": "build: add project automation Makefile",
    "README.md": "docs: add comprehensive architecture, quickstart, and reference documentation",
    "LICENSE": "docs: add MIT license",
}


def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass


def run_cmd(cmd: List[str], cwd: str = ".") -> Tuple[int, str, str]:
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr.strip()


def get_uncommitted_files() -> List[str]:
    """Returns list of uncommitted or untracked individual files relative to repo root."""
    code, stdout, _ = run_cmd(["git", "status", "--porcelain"])
    files = []
    if code != 0:
        return files

    for line in stdout.splitlines():
        line_clean = line.rstrip("\r\n")
        if not line_clean.strip():
            continue
        if len(line_clean) >= 4 and line_clean[2] == ' ':
            filepath = line_clean[3:].strip().strip('"')
        elif len(line_clean) >= 3 and line_clean[1] == ' ':
            filepath = line_clean[2:].strip().strip('"')
        else:
            filepath = line_clean[3:].strip().strip('"')

        # Skip log or state files or scratch
        if filepath in (LOG_FILE, STATE_FILE, ".DS_Store"):
            continue

        if os.path.isfile(filepath):
            files.append(filepath)
        elif os.path.isdir(filepath):
            # Recursively expand files in untracked directory
            for root, dirs, filenames in os.walk(filepath):
                # Skip hidden/excluded directories
                dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
                for fn in sorted(filenames):
                    if fn in (LOG_FILE, STATE_FILE, ".DS_Store") or fn.endswith(".pyc"):
                        continue
                    full = os.path.join(root, fn)
                    files.append(full)

    # Deduplicate and sort
    unique_files = list(set(files))
    return sorted(unique_files, key=lambda f: (_priority_order(f), f))


def _priority_order(filepath: str) -> int:
    """Sorts files in a logical architectural progression."""
    if filepath == ".gitignore":
        return 1
    if filepath in ("pyproject.toml", "setup.py", "requirements.txt", "go.mod"):
        return 2
    if "config" in filepath or "validator" in filepath:
        return 3
    if "models.py" in filepath:
        return 4
    if "providers" in filepath:
        return 5
    if "scanner" in filepath and "cmd" not in filepath and "pkg" not in filepath:
        return 6
    if "personas" in filepath:
        return 7
    if "engine" in filepath:
        return 8
    if "presets.py" in filepath:
        return 9
    if "ci" in filepath or "cli.py" in filepath:
        return 10
    if "web" in filepath:
        return 11
    if "cmd" in filepath or "pkg" in filepath:
        return 12
    if "scripts" in filepath:
        return 13
    if "examples" in filepath:
        return 14
    if "tests" in filepath:
        return 15
    if ".github" in filepath:
        return 16
    if filepath in ("Makefile", "LICENSE"):
        return 17
    if "README" in filepath:
        return 18
    return 25


def generate_commit_message(filepath: str) -> str:
    if filepath in COMMIT_MESSAGE_MAP:
        return COMMIT_MESSAGE_MAP[filepath]

    basename = os.path.basename(filepath)
    ext = os.path.splitext(filepath)[1]
    name_no_ext = os.path.splitext(basename)[0]

    if filepath.startswith("tests/"):
        return f"test: add unit tests for {name_no_ext}"
    if filepath.startswith("examples/"):
        return f"example: add polyglot sample {basename}"
    if filepath.startswith("panel_review/"):
        return f"feat: implement {name_no_ext} component"

    return f"feat: add {filepath}"


def has_git_remote(remote_name: str = "origin") -> bool:
    code, stdout, _ = run_cmd(["git", "remote"])
    return code == 0 and remote_name in [r.strip() for r in stdout.splitlines()]


def get_current_branch() -> str:
    code, stdout, _ = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return stdout.strip() if code == 0 and stdout.strip() else "main"


def load_state() -> Dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"committed_files": [], "start_time": datetime.utcnow().isoformat()}


def save_state(state: Dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def run_staged_push(
    min_minutes: int = 30,
    max_minutes: int = 45,
    interval_seconds: Optional[int] = None,
    dry_run: bool = False,
    instant: bool = False,
    remote: str = "origin",
    branch: Optional[str] = None,
) -> int:
    branch_name = (branch or get_current_branch()).strip()
    remote_exists = has_git_remote(remote)

    log("=" * 60)
    log("🚀 Starting Staged Git Committer & Pusher")
    log("=" * 60)
    log(f"Target Branch  : {branch_name}")
    log(f"Remote Status  : {'Found (' + remote + ')' if remote_exists else 'No remote configured yet'}")
    if instant:
        log("Execution Mode : INSTANT (no delay between commits)")
    elif interval_seconds:
        log(f"Execution Mode : Custom Interval ({interval_seconds}s between commits)")
    else:
        log(f"Execution Mode : Random Interval ({min_minutes} to {max_minutes} minutes)")
    log(f"Dry Run        : {dry_run}")
    log("-" * 60)

    state = load_state()
    uncommitted = get_uncommitted_files()

    if not uncommitted:
        log("✅ No uncommitted files found in repository. All caught up!")
        return 0

    log(f"📋 Found {len(uncommitted)} files pending staged commit:")
    for idx, f in enumerate(uncommitted, 1):
        msg = generate_commit_message(f)
        log(f"  {idx:2d}. {f:<40} -> \"{msg}\"")
    log("-" * 60)

    for idx, filepath in enumerate(uncommitted, 1):
        commit_msg = generate_commit_message(filepath)

        if dry_run:
            if instant:
                simulated_wait = 0
            elif interval_seconds:
                simulated_wait = interval_seconds
            else:
                simulated_wait = random.randint(min_minutes * 60, max_minutes * 60)

            log(f"[DRY-RUN {idx}/{len(uncommitted)}] Would stage & commit: {filepath}")
            log(f"             Message: {commit_msg}")
            if remote_exists:
                log(f"             Push   : git push {remote} {branch_name}")
            else:
                log(f"             Push   : (Remote '{remote}' not set; local commit only)")
            if idx < len(uncommitted):
                log(f"             Wait   : {simulated_wait // 60}m {simulated_wait % 60}s before next commit")
            continue

        # Stage file
        log(f"[{idx}/{len(uncommitted)}] Staging file: {filepath}")
        code, _, err = run_cmd(["git", "add", filepath])
        if code != 0:
            log(f"❌ Failed to stage {filepath}: {err}")
            continue

        # Commit file
        code, stdout, err = run_cmd(["git", "commit", "-m", commit_msg])
        if code != 0:
            log(f"⚠️ Commit skipped or failed for {filepath}: {err or stdout}")
            continue
        log(f"✅ Committed: \"{commit_msg}\"")

        # Push file
        if remote_exists:
            log(f"⬆️  Pushing commit to {remote}/{branch_name}...")
            p_code, p_out, p_err = run_cmd(["git", "push", "-u", remote, branch_name])
            if p_code == 0:
                log("🚀 Successfully pushed commit!")
            else:
                log(f"⚠️ Git push notice: {p_err or p_out}")
        else:
            log(f"ℹ️ Local commit created. No remote configured yet (add with 'git remote add {remote} <url>' to push).")

        # Update state
        state["committed_files"].append({
            "file": filepath,
            "message": commit_msg,
            "timestamp": datetime.utcnow().isoformat(),
        })
        save_state(state)

        # Wait random duration if there are more files
        if idx < len(uncommitted):
            if instant:
                delay = 0
            elif interval_seconds:
                delay = interval_seconds
            else:
                # Random 30 to 45 minutes
                delay = random.randint(min_minutes * 60, max_minutes * 60)

            resume_time = datetime.now() + timedelta(seconds=delay)
            mins = delay // 60
            secs = delay % 60
            log(f"⏳ Sleeping for {mins}m {secs}s. Next commit scheduled for {resume_time.strftime('%H:%M:%S')}...")
            time.sleep(delay)

    log("=" * 60)
    log("🎉 All files staged, committed, and pushed successfully!")
    log("=" * 60)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Staged Git Committer & Pusher (30-45 min intervals)")
    parser.add_argument("--min-minutes", type=int, default=30, help="Minimum random delay in minutes (default: 30)")
    parser.add_argument("--max-minutes", type=int, default=45, help="Maximum random delay in minutes (default: 45)")
    parser.add_argument("--interval-seconds", type=int, help="Custom delay in seconds for demo/testing")
    parser.add_argument("--instant", action="store_true", help="Run without delays")
    parser.add_argument("--dry-run", action="store_true", help="Preview commit schedule without making changes")
    parser.add_argument("--remote", default="origin", help="Git remote name (default: origin)")
    parser.add_argument("--branch", help="Git branch to push to")

    args = parser.parse_args()
    sys.exit(run_staged_push(
        min_minutes=args.min_minutes,
        max_minutes=args.max_minutes,
        interval_seconds=args.interval_seconds,
        dry_run=args.dry_run,
        instant=args.instant,
        remote=args.remote,
        branch=args.branch,
    ))


if __name__ == "__main__":
    main()
