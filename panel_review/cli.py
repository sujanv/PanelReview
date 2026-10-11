"""
Command Line Interface (CLI) for PanelReview.
"""

import os
import sys
import argparse
import shutil
from panel_review.config import load_config
from panel_review.scanner.repo_scanner import RepoScanner
from panel_review.scanner.git_inspector import GitInspector
from panel_review.engine.reviewer import ReviewEngine
from panel_review.engine.report import ReportGenerator
from panel_review.engine.sarif import SarifExporter
from panel_review.engine.deliberation import DeliberationEngine
from panel_review.engine.remediator import PatchRemediator
from panel_review.presets import PRESETS, apply_preset
from panel_review.providers.factory import ProviderFactory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="panel-review",
        description="AI-based Multi-Persona Agent Panel Review System for Polyglot Codebases",
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # Review command
    review_p = subparsers.add_parser("review", help="Run a panel review on a local path, git diff, or remote git repo")
    review_p.add_argument("--path", "-p", default=".", help="Local path or directory to review (default: .)")
    review_p.add_argument("--repo", "-r", help="Remote Git repository URL to clone and review")
    review_p.add_argument("--branch", "-b", help="Git branch to review")
    review_p.add_argument("--diff", action="store_true", help="Review only git diff / uncommitted changes")
    review_p.add_argument("--config", "-c", help="Path to custom panel_config.yaml or panel_config.json")
    review_p.add_argument("--preset", choices=list(PRESETS.keys()), help="Apply review preset (e.g. security-strict, sre-readiness)")
    review_p.add_argument("--deliberate", action="store_true", help="Conduct multi-persona cross-examination deliberation round")
    review_p.add_argument("--provider", help="Override default LLM provider (openai, anthropic, gemini, ollama, mock)")
    review_p.add_argument("--model", "-m", help="Override default LLM model name")
    review_p.add_argument("--max-files", type=int, default=50, help="Max files to scan for review (default: 50)")
    review_p.add_argument("--output-md", default="panel_review_report.md", help="Path for markdown report")
    review_p.add_argument("--output-html", default="panel_review_report.html", help="Path for interactive HTML report")
    review_p.add_argument("--output-json", default=None, help="Path for JSON report")
    review_p.add_argument("--output-sarif", default=None, help="Path for SARIF v2.1.0 report for GitHub Security Alerts")

    # Fix command
    fix_p = subparsers.add_parser("fix", help="Generate automated patch fixes for review findings")
    fix_p.add_argument("--path", "-p", default=".", help="Target directory to inspect and generate fixes for")
    fix_p.add_argument("--output-patch", default="panel_review_fixes.patch", help="Path to output unified diff patch file")

    # Serve command
    serve_p = subparsers.add_parser("serve", help="Launch the local live Web Dashboard GUI server")
    serve_p.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")

    # Presets command
    subparsers.add_parser("presets", help="List available review presets")

    # Personas command
    personas_p = subparsers.add_parser("personas", help="List configured panel review personas")
    personas_p.add_argument("--config", "-c", help="Path to config file")

    # Models command
    models_p = subparsers.add_parser("models", help="Test connectivity to configured AI model providers")
    models_p.add_argument("--config", "-c", help="Path to config file")

    # Staged Push command
    staged_p = subparsers.add_parser("staged-push", help="Commit and push repository files one at a time with random delays")
    staged_p.add_argument("--min-minutes", type=int, default=30, help="Minimum random delay in minutes (default: 30)")
    staged_p.add_argument("--max-minutes", type=int, default=45, help="Maximum random delay in minutes (default: 45)")
    staged_p.add_argument("--dry-run", action="store_true", help="Preview staged commit schedule without executing")
    staged_p.add_argument("--instant", action="store_true", help="Execute without delays for testing/demo")
    staged_p.add_argument("--remote", default="origin", help="Git remote name (default: origin)")
    staged_p.add_argument("--branch", help="Git branch to push to (default: current branch)")

    # Init Config command
    init_p = subparsers.add_parser("init-config", help="Initialize a sample panel_config.yaml or json")
    init_p.add_argument("--format", choices=["yaml", "json"], default="yaml", help="Configuration format")

    return parser


def handle_review(args: argparse.Namespace) -> int:
    config = load_config(args.config)

    # CLI Overrides
    if args.provider:
        config.default_provider = args.provider
    if args.model:
        config.default_model = args.model

    if args.preset:
        preset_info = PRESETS[args.preset]
        print(f"Applying Preset  : [{args.preset}] - {preset_info['description']}")
        active_set = set(preset_info["active_persona_ids"])
        for p in config.personas:
            p.enabled = p.id in active_set

    print(f"\n==========================================================")
    print(f"🏛️  AI Agent Panel Review System v1.0")
    print(f"==========================================================")
    print(f"Default Provider : {config.default_provider}")
    print(f"Default Model    : {config.default_model}")
    print(f"Active Personas  : {len(config.get_enabled_personas())}")

    temp_clone_dir = None
    git_inspector = GitInspector(config.scanner)

    try:
        if args.repo:
            print(f"\n[1/3] 🌐 Cloning remote git repository: {args.repo}...")
            repo_info, temp_clone_dir = git_inspector.clone_remote(
                git_url=args.repo,
                branch=args.branch,
            )
        elif args.diff:
            print(f"\n[1/3] 🔍 Analyzing git diff in: {os.path.abspath(args.path)}...")
            repo_info = git_inspector.inspect_diff(args.path, target_ref=args.branch or "HEAD")
        else:
            print(f"\n[1/3] 📂 Scanning local directory: {os.path.abspath(args.path)}...")
            scanner = RepoScanner(config.scanner)
            repo_info = scanner.scan_directory(args.path, max_files=args.max_files)

        print(f"      Scanned {repo_info.total_files} files ({repo_info.total_lines} lines of code).")
        langs_summary = ", ".join([f"{k}: {v}" for k, v in repo_info.languages.items()])
        print(f"      Languages detected: {langs_summary or 'None'}")

        if not repo_info.files:
            print("⚠️  No matching code files found to review. Exiting.")
            return 1

        print(f"\n[2/3] 🧑‍💻 Convening Panel Review Board...")
        engine = ReviewEngine(config)

        def on_persona_start(persona, prov, model):
            print(f"      ▶️  {persona.emoji} {persona.name} evaluating via [{prov}:{model}]...")

        def on_persona_complete(result):
            print(f"      ✅ {result.persona_emoji} {result.persona_name} completed (Score: {result.score}/100, Findings: {len(result.findings)})")

        report = engine.run_review(
            repo_info=repo_info,
            on_persona_start=on_persona_start,
            on_persona_complete=on_persona_complete,
        )

        # Optional Deliberation Round
        if args.deliberate:
            print(f"\n🗣️  Conducting Multi-Persona Deliberation & Cross-Examination Round...")
            transcript = DeliberationEngine.conduct_deliberation(report.persona_results)
            print(f"      Conducted {transcript.rounds_conducted} cross-domain debate exchanges.")
            report.executive_summary += f"\n\n{transcript.to_markdown()}"

        print(f"\n[3/3] ⚖️  Panel Consensus Synthesized!")
        print(f"      Overall Verdict     : {report.overall_verdict.value}")
        print(f"      Overall Health Score: {report.overall_score}/100")
        print(f"      Total Findings      : {len(report.consolidated_findings)}")

        # Write reports
        if args.output_md:
            md_content = ReportGenerator.to_markdown(report)
            with open(args.output_md, "w", encoding="utf-8") as f:
                f.write(md_content)
            print(f"\n📄 Markdown Report saved to : {os.path.abspath(args.output_md)}")

        if args.output_html:
            html_content = ReportGenerator.to_html(report)
            with open(args.output_html, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"🌐 HTML Dashboard saved to  : {os.path.abspath(args.output_html)}")

        if args.output_json:
            json_content = ReportGenerator.to_json(report)
            with open(args.output_json, "w", encoding="utf-8") as f:
                f.write(json_content)
            print(f"📊 JSON Report saved to     : {os.path.abspath(args.output_json)}")

        if args.output_sarif:
            sarif_content = SarifExporter.to_sarif_json(report)
            with open(args.output_sarif, "w", encoding="utf-8") as f:
                f.write(sarif_content)
            print(f"🛡️  SARIF Report saved to    : {os.path.abspath(args.output_sarif)}")

        print("\n✨ Panel Review finished successfully!\n")
        return 0

    finally:
        if temp_clone_dir and os.path.exists(temp_clone_dir):
            shutil.rmtree(temp_clone_dir, ignore_errors=True)


def handle_fix(args: argparse.Namespace) -> int:
    config = load_config()
    scanner = RepoScanner(config.scanner)
    repo_info = scanner.scan_directory(args.path)
    engine = ReviewEngine(config)
    print(f"🔍 Analyzing {repo_info.total_files} files to generate remediation patches...")
    report = engine.run_review(repo_info)
    patches = PatchRemediator.generate_all_patches(report, base_dir=args.path)

    if not patches:
        print("✅ No automated patches generated for identified code.")
        return 0

    patch_file = PatchRemediator.export_unified_patch_file(patches, output_path=args.output_patch)
    print(f"\n🛠️ Generated {len(patches)} remediation patches in unified diff format:")
    for idx, p in enumerate(patches, 1):
        print(f"  {idx}. [{p.file_path}:{p.line_number}] {p.finding_title}")
    print(f"\n💾 Saved unified patch file to: {os.path.abspath(patch_file)}")
    print(f"👉 Apply with: git apply {args.output_patch}\n")
    return 0


def handle_serve(args: argparse.Namespace) -> int:
    from panel_review.web.server import start_dashboard_server
    start_dashboard_server(port=args.port)
    return 0


def handle_presets() -> int:
    print("\n📋 Available Panel Review Presets:\n")
    for name, info in PRESETS.items():
        print(f"  * {name:<22} - {info['description']}")
        print(f"    Personas: {', '.join(info['active_persona_ids'])} (Min Score: {info['min_approval_score']})\n")
    return 0


def handle_personas(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    print(f"\n🏛️  Configured Panel Review Personas ({len(config.personas)} total):\n")
    for p in config.personas:
        prov, mod = config.get_persona_provider(p)
        status = "ENABLED" if p.enabled else "DISABLED"
        print(f"{p.emoji} {p.name} [{status}]")
        print(f"   Title   : {p.title}")
        print(f"   Provider: {prov} | Model: {mod}")
        print(f"   Min Sev : {p.severity_threshold}")
        print(f"   Focus   : {', '.join(p.focus_areas[:3])}...")
        print()
    return 0


def handle_models(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    print("\n🔌 Testing AI Model Provider Connections:\n")
    tested = set()
    for prov_name in config.providers.keys():
        if prov_name in tested:
            continue
        tested.add(prov_name)
        try:
            prov = ProviderFactory.create(prov_name, config)
            res = prov.test_connection()
            status = "✅ ONLINE" if res["status"] == "success" else f"❌ {res['message']}"
            print(f"  [{prov_name.upper():<10}] Model: {prov.model:<24} Status: {status}")
        except Exception as e:
            print(f"  [{prov_name.upper():<10}] Status: ❌ {e}")
    print()
    return 0


def handle_staged_push(args: argparse.Namespace) -> int:
    from scripts.staged_git_pusher import run_staged_push
    return run_staged_push(
        min_minutes=args.min_minutes,
        max_minutes=args.max_minutes,
        dry_run=args.dry_run,
        instant=args.instant,
        remote=args.remote,
        branch=args.branch,
    )


def main() -> int:
    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    args = parser.parse_args()
    if args.command == "review":
        return handle_review(args)
    elif args.command == "fix":
        return handle_fix(args)
    elif args.command == "serve":
        return handle_serve(args)
    elif args.command == "presets":
        return handle_presets()
    elif args.command == "personas":
        return handle_personas(args)
    elif args.command == "models":
        return handle_models(args)
    elif args.command == "staged-push":
        return handle_staged_push(args)
    elif args.command == "init-config":
        print("Configuration file already initialized (panel_config.yaml and panel_config.json).")
        return 0
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
