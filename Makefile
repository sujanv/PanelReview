.PHONY: help test review review-sample fix presets sarif serve personas models validate trends pr-comment dry-run-push staged-push clean

help:
	@echo "Available commands for AI Agent Panel Review:"
	@echo "  make test             - Run complete automated test suite"
	@echo "  make review           - Run panel review on current directory"
	@echo "  make review-sample    - Run panel review on sample polyglot project"
	@echo "  make fix              - Generate automated code remediation patch"
	@echo "  make presets          - List available review presets"
	@echo "  make sarif            - Run review and export SARIF v2.1.0 for GitHub Alerts"
	@echo "  make serve            - Start live local Web Dashboard GUI"
	@echo "  make personas         - List all configured panel personas"
	@echo "  make models           - Test connectivity to configured AI model providers"
	@echo "  make validate         - Validate configuration schema and environment API keys"
	@echo "  make trends           - View historical codebase health and regression trends"
	@echo "  make pr-comment       - Generate Pull Request review comment markdown"
	@echo "  make dry-run-push     - Preview staged file-by-file commits schedule"
	@echo "  make staged-push      - Start staged git commit & push (random 30-45m delay)"
	@echo "  make clean            - Clean generated reports and caches"

validate:
	python3 -m panel_review.cli validate-config

trends:
	python3 -m panel_review.cli trends

pr-comment:
	python3 -m panel_review.cli pr-comment --path .

fix:
	python3 -m panel_review.cli fix --path .

presets:
	python3 -m panel_review.cli presets

sarif:
	python3 -m panel_review.cli review --path . --output-sarif panel_review.sarif

serve:
	python3 -m panel_review.cli serve --port 8080

test:
	python3 -m unittest discover -s tests

review:
	python3 -m panel_review.cli review --path .

review-sample:
	python3 -m panel_review.cli review --path examples/sample_polyglot_project

personas:
	python3 -m panel_review.cli personas

models:
	python3 -m panel_review.cli models

dry-run-push:
	python3 scripts/staged_git_pusher.py --dry-run

staged-push:
	python3 scripts/staged_git_pusher.py --min-minutes 30 --max-minutes 45

clean:
	rm -rf __pycache__ */__pycache__ */*/__pycache__ panel_review_report.* staged_pusher.log .staged_pusher_state.json
