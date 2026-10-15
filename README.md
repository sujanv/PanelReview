# 🏛️ PanelReview: AI-Powered Multi-Persona Agent Panel Review System

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Zero-Dependency Core](https://img.shields.io/badge/core-zero--dependency-green.svg)](https://docs.python.org/3/library/)
[![Polyglot Support](https://img.shields.io/badge/polyglot-25%2B%20languages-purple.svg)](#polyglot-language-support)

**PanelReview** is an enterprise-grade, multi-agent AI panel review system. Rather than relying on a single generic code review prompt, PanelReview convenes a **board of specialized AI personas**—each scrutinizing the codebase from their dedicated domain of expertise—followed by an executive consensus synthesis by the **Panel Chair**.

---

## 🌟 Key Highlights

- 🧑‍💻 **Configurable Expert Personas**: Includes Security Engineer (OWASP/threat modeling), Observability & SRE Engineer, Performance & Scalability Engineer, Software Architect, QA & Reliability Engineer, and Compliance & Privacy Specialist. Add custom personas with simple YAML/JSON configurations.
- 🤖 **Universal AI Model / Provider Support**: Configurable to use any AI model globally or per persona:
  - **OpenAI** (`gpt-4o`, `gpt-4o-mini`, `o1`, `o3-mini`)
  - **Anthropic** (`claude-3-7-sonnet`, `claude-3-5-sonnet`, `claude-3-haiku`)
  - **Google Gemini** (`gemini-1.5-pro`, `gemini-1.5-flash`, `gemini-2.0-flash`)
  - **Ollama / Local LLMs** (`llama3.3`, `deepseek-r1`, `mistral`, `codellama`)
  - **OpenAI-Compatible Custom Endpoints** (Groq, Together AI, OpenRouter, vLLM, LMStudio)
  - **Built-in Mock/Offline Provider**: Zero-cost heuristic review for local testing, CI/CD, and demo without requiring API keys.
- 🔑 **Deep Secret & Credential Scanner**: Integrated AST regex patterns and Shannon entropy heuristics to detect exposed AWS keys, GitHub PATs, JWTs, Stripe keys, SSH keys, and database connection URIs with safe masking.
- 🗳️ **Multi-Model Consensus Voting Strategies**: Choose how the panel aggregates scores and findings: `weighted_domain` (Security 1.5x, SRE 1.3x), `borda_count` (ranked choice), `pessimistic_worst_case` (strictest security veto), or `simple_average`.
- 📈 **Historical Health & Regression Tracker**: Track codebase quality over time (`.panel_review_history.json`), monitor score deltas, and alert on quality or security regressions across runs.
- 🤖 **CI/CD Pull Request Review Bot**: Formats rich markdown comments for GitHub and GitLab pull requests with status badges, score gauges, collapsible per-persona finding summaries, and action checklists.
- ✅ **Configuration Validator & Linter**: Verifies YAML/JSON schema, provider model declarations, and environment variable API key readiness (`panel-review validate-config`).
- 🌐 **Polyglot Codebase Compatibility**: Automatically detects and reviews 25+ programming and infrastructure languages including Python, Go, Rust, TypeScript, JavaScript, Java, C/C++, C#, Ruby, PHP, Swift, Kotlin, Shell, SQL, Terraform, and Dockerfiles.
- 🔍 **Flexible Review Scope**:
  - **Local Workspace**: Inspect any folder, package, or file.
  - **Git Diff Mode**: Inspect only uncommitted, staged, or branch diff changes (`--diff`).
  - **Remote Git Source Control**: Clone and review any remote Git repository URL (`--repo https://...`) on any branch or tag.
- ⏱️ **Automated Staged Git Committer & Pusher**: Built-in automator (`scripts/staged_git_pusher.py` or `panel-review staged-push`) that commits and pushes repository files **one at a time with randomized 30 to 45 minute intervals**, complete with state persistence, automated semantic commit messages, and graceful remote fallback.
- 🛡️ **SARIF v2.1.0 & GitHub Code Scanning**: Direct export of findings to standard SARIF format (`--output-sarif`) for automatic integration with GitHub Security Alerts and CI/CD pipelines.
- 🛠️ **Automated Code Remediation & Patching**: Generates git-applyable unified diffs and surgical patches (`panel-review fix`) for identified security and quality findings.
- 🗣️ **Multi-Persona Deliberation & Cross-Examination**: Personas actively cross-examine each other's findings (`--deliberate`) to reconcile performance, security, and telemetry trade-offs.
- 🌐 **Live Web Dashboard GUI**: Zero-dependency local web server (`panel-review serve`) for live browser inspection and real-time finding filtering.
- ⚡ **High-Speed Go Scanner Companion**: Reusable Go package (`pkg/scanner/`) and CLI tool (`cmd/panel-scanner/`) for high-throughput repository scanning and token profiling.
- 📋 **Specialized Review Presets**: Instantly trigger domain presets (`--preset security-strict`, `sre-readiness`, `clean-architecture`, `quick-scan`, `full-audit`).
- 📊 **Multi-Format Deliverables**: Generates comprehensive **Markdown Reports**, interactive standalone **HTML Dashboards** with score ring gauges and filterable finding tables, and machine-readable **JSON / SARIF** exports.

---

## 🏛️ Architecture Overview

```
                      ┌──────────────────────────────────────────┐
                      │   Target Codebase (Local / Diff / Git)   │
                      └────────────────────┬─────────────────────┘
                                           │
                         RepoScanner & SecretScanner (Entropy)
                                           │
       ┌───────────────────┬───────────────┴───────────────┬───────────────────┐
       ▼                   ▼                               ▼                   ▼
┌──────────────┐    ┌──────────────┐                ┌──────────────┐    ┌──────────────┐
│  🛡️ Security  │    │ 📡 Observ-   │    ... (QA,    │⚡ Performance│    │ 🏗️ Architect │
│   Engineer   │    │   ability    │    Compliance) │   Engineer   │    │   Persona    │
└──────┬───────┘    └──────┬───────┘                └──────┬───────┘    └──────┬───────┘
       │ [Claude]          │ [GPT-4o]                      │ [DeepSeek]        │ [Gemini]
       └───────────────────┼───────────────────────────────┴───────────────────┘
                           │ (Concurrent Multi-Threaded Execution)
                           ▼
              ┌───────────────────────────┐
              │  ⚖️  Panel Review Chair    │  (Consensus Voting & Deliberation)
              └────────────┬──────────────┘
                           │
         ┌─────────────────┼─────────────────┬─────────────────┐
         ▼                 ▼                 ▼                 ▼
 📄 Markdown Report  🌐 HTML Dashboard  🛡️ SARIF v2.1.0  🤖 PR Comment
```

---

## 🚀 Quickstart

### 1. Requirements & Setup
PanelReview runs on standard Python 3.9+ with **zero required external packages** using Python's built-in standard library.

```bash
# Clone the repository
git clone https://github.com/sujanv/PanelReview.git
cd PanelReview

# (Optional) Install enhanced packages for YAML formatting and rich console output
pip install -r requirements.txt
```

### 2. Run a Panel Review

```bash
# Review current directory using the built-in mock provider (no API keys required!)
python3 -m panel_review.cli review --path .

# Review the included polyglot sample project
python3 -m panel_review.cli review --path examples/sample_polyglot_project

# Review only git diff / uncommitted changes
python3 -m panel_review.cli review --diff

# Review a remote Git repository
python3 -m panel_review.cli review --repo https://github.com/expressjs/express.git --branch master

# Run review with custom consensus strategy and record historical trend
python3 -m panel_review.cli review --path . --strategy borda_count --record-trend
```

### 3. Inspect the Output
After running, PanelReview generates:
- `panel_review_report.md` — Complete markdown report for pull requests or documentation.
- `panel_review_report.html` — Interactive HTML report you can open directly in any browser.
- `.panel_review_history.json` — Historical health scores snapshot (when `--record-trend` is passed).

---

## ⚙️ Configuration & Model Flexibility

Configure the panel in `panel_config.yaml` or `panel_config.json`:

```yaml
version: "1.0"

# Default Model Provider: "openai", "anthropic", "gemini", "ollama", "custom", or "mock"
default_provider: "anthropic"
default_model: "claude-3-5-sonnet-20241022"

providers:
  openai:
    api_key_env: "OPENAI_API_KEY"
    model: "gpt-4o"
    temperature: 0.2

  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
    model: "claude-3-5-sonnet-20241022"
    temperature: 0.2

  gemini:
    api_key_env: "GEMINI_API_KEY"
    model: "gemini-1.5-pro"
    temperature: 0.2

  ollama:
    base_url: "http://localhost:11434"
    model: "llama3.3"
    temperature: 0.2

  custom:
    api_key_env: "CUSTOM_API_KEY"
    base_url: "https://api.groq.com/openai/v1"
    model: "llama-3.3-70b-versatile"

# Personas: Mix and match models per persona
personas:
  - id: "security"
    enabled: true
    name: "Security Engineer"
    provider: "anthropic" # Security uses Claude
    model: "claude-3-5-sonnet-20241022"
    severity_threshold: "LOW"

  - id: "observability"
    enabled: true
    name: "Observability & SRE Engineer"
    provider: "openai" # Observability uses GPT-4o
    model: "gpt-4o"
    severity_threshold: "MEDIUM"

  - id: "performance"
    enabled: true
    name: "Performance & Scalability Engineer"
    provider: "ollama" # Performance uses local Llama
    model: "llama3.3"
    severity_threshold: "MEDIUM"
```

---

## 🧑‍💻 The Panel Personas

| Persona | Title | Core Focus Areas |
| :--- | :--- | :--- |
| 🛡️ **Security Engineer** | AppSec & Threat Modeling Specialist | OWASP Top 10, CWE, hardcoded secrets, injection vectors, authentication, CSRF/SSRF, cryptography |
| 📡 **Observability Engineer** | SRE & Telemetry Specialist | Structured logging, OpenTelemetry tracing, RED/USE metrics, network timeouts, retries, health probes |
| ⚡ **Performance Engineer** | High-Throughput & Efficiency Specialist | $O(N^2)$ algorithmic complexity, memory leaks, connection pools, N+1 queries, race conditions, caching |
| 🏗️ **Software Architect** | Clean Architecture & Design Specialist | SOLID & DRY principles, modularity, coupling/cohesion, API ergonomics, maintainability |
| 🧪 **QA & Reliability Engineer** | Test Engineering & Edge Case Specialist | Testability, boundary conditions, nil/null safety, mockability, unhandled exceptions, deterministic tests |
| 📜 **Compliance & Privacy** | Data Governance Specialist | GDPR/CCPA PII protection, data retention, license compliance (GPL/MIT/Apache), audit trails |
| ⚖️ **Panel Review Chair** | Consensus & Executive Moderator | Board synthesis, cross-persona deduplication, calibrated scoring (0-100), final verdict |

---

## 🔑 Secret & Credential Scanning

PanelReview automatically detects committed secrets, authentication credentials, and high-entropy API tokens prior to invoking LLMs:

- **Known Signatures**:
  - AWS Access Key IDs (`AKIA...`)
  - GitHub Personal Access Tokens (`ghp_...`, `gho_...`)
  - JSON Web Tokens (`eyJ...`)
  - Stripe Secret Keys (`sk_live_...`, `rk_live_...`)
  - SSH / RSA Private Key headers (`BEGIN RSA PRIVATE KEY`)
  - Database URIs (`postgres://user:pass@host/db`)
- **Shannon Entropy Heuristic**: Flags variable assignments containing random strings exceeding an entropy threshold of $4.5$, catching undisclosed API keys.
- **Safe Masking**: Detected credentials in reports and SARIF alerts are automatically masked (`AKIA************MPLE`) to prevent secret leakage in review logs.

---

## 🗳️ Multi-Model Consensus Voting Strategies

Customize how individual persona scores are combined into the final verdict using the `--strategy` option:

1. **`weighted_domain` (Default)**: Domain-weighted consensus placing higher priority on critical engineering disciplines:
   - Security: $1.5\times$
   - Observability & SRE: $1.3\times$
   - Architecture & Performance: $1.2\times$
   - Compliance: $1.1\times$
   - QA: $1.0\times$
2. **`borda_count`**: Ranked-choice tournament voting where personas rank each other's score distributions, mitigating single-model bias.
3. **`pessimistic_worst_case`**: Security-first conservative strategy where the overall score is anchored to the minimum score awarded by any single persona.
4. **`simple_average`**: Arithmetic mean across all active personas.

```bash
# Example: Apply pessimistic worst-case consensus
panel-review review --path . --strategy pessimistic_worst_case
```

---

## 📈 Historical Health Trends & Regression Tracking

Track your codebase's quality evolution across commits and CI runs:

```bash
# Record current review snapshot to .panel_review_history.json
panel-review review --path . --record-trend

# View historical score trends and quality regressions
panel-review trends

# Or using Makefile
make trends
```

Output includes:
- Run timestamps and commit/branch metadata
- Health score trend over time
- Critical finding count evolution
- Regression alerts (e.g., score drops $> 5$ points or newly introduced critical findings)

---

## 🤖 CI/CD Pull Request Review Bot

Generate clean, actionable review comments ready to be posted directly by GitHub Actions or GitLab CI:

```bash
# Generate PR comment markdown
panel-review pr-comment --path . --output pr_comment.md

# Or using Makefile
make pr-comment
```

The generated markdown includes:
- Overall status badge (`APPROVED`, `APPROVED_WITH_CONDITIONS`, or `REJECTED`)
- Required action checklist for pull request authors
- Persona evaluation summary table
- Expandable `<details>` accordions per persona with exact file paths and line numbers
- Code suggestion blocks for direct application

---

## ✅ Configuration Validator & Environment Linter

Verify your configuration files and provider API keys before running reviews:

```bash
# Validate default panel_config.yaml or panel_config.json
panel-review validate-config

# Validate a custom configuration file
panel-review validate-config --config my_custom_config.yaml

# Or using Makefile
make validate
```

Checks performed:
- Validates JSON/YAML structure and version compatibility
- Confirms provider definitions and model identifiers
- Verifies unique persona IDs
- Checks environment variables for configured API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.)

---

## ⚡ High-Speed Go Scanner Companion

For enterprise mono-repos, PanelReview includes a high-throughput Go scanner:

- **Package**: `pkg/scanner/` provides reusable scanning and AST secret pattern detection.
- **CLI**: `cmd/panel-scanner/` compiles to a native binary for microsecond repository walking.

```bash
# Build and run the Go scanner
go run cmd/panel-scanner/main.go --path .
```

---

## ⏱️ Staged Git Committer & Pusher (30-45 Minute Random Interval)

The project includes an automated script that stages, creates meaningful conventional commits, and pushes files to Git **one at a time with randomized 30 to 45 minute intervals**.

### Features:
- 🎲 **Random Delay**: Waits between 30 and 45 minutes randomly before committing the next file (`random.randint(1800, 2700)` seconds).
- 💾 **State Persistence**: Progress is saved to `.staged_pusher_state.json`. If stopped or rebooted, it automatically resumes from where it left off.
- 📝 **Intelligent Commit Messages**: Generates architectural commit messages per file (`feat(validator)`, `feat(scanner)`, `feat(engine)`, etc.).
- 🌐 **Remote Handling**: Pushes automatically if a Git remote exists; logs gracefully if running locally.

### Usage:

```bash
# Preview the commit schedule and random delay simulation (Dry Run)
python3 scripts/staged_git_pusher.py --dry-run
# or
make dry-run-push

# Run with standard 30 to 45 minute randomized interval
python3 scripts/staged_git_pusher.py --min-minutes 30 --max-minutes 45
# or
make staged-push

# Instant mode (commit all one by one immediately without waiting)
python3 scripts/staged_git_pusher.py --instant

# Fast demo mode (5 second interval between commits)
python3 scripts/staged_git_pusher.py --interval-seconds 5

# Or use the CLI alias
python3 -m panel_review.cli staged-push --min-minutes 30 --max-minutes 45
```

---

## 🛠️ CLI Reference

```
usage: panel-review [-h] {review,fix,pr-comment,trends,validate-config,serve,presets,personas,models,staged-push,init-config} ...

Subcommands:
  review           Run a panel review on a local path, git diff, or remote git repo
  fix              Generate automated patch fixes for identified review findings
  pr-comment       Generate a GitHub/GitLab Pull Request review comment markdown
  trends           View historical codebase health and score regression trends
  validate-config  Validate configuration file schema and environment API keys
  serve            Launch the local live Web Dashboard GUI server
  presets          List available specialized review presets
  personas         List configured panel review personas and their assigned models
  models           Test connectivity to configured AI model providers
  staged-push      Commit and push repository files one at a time with random delays
  init-config      Initialize a sample configuration file
```

### Key Flags for `panel-review review`:
- `--path, -p <dir>`: Target local directory or file (default: `.`)
- `--repo, -r <url>`: Remote Git repository URL to clone and review
- `--branch, -b <branch>`: Target branch name
- `--diff`: Inspect only Git diff / uncommitted changes
- `--preset <name>`: Apply review preset (`security-strict`, `sre-readiness`, `clean-architecture`, etc.)
- `--strategy <name>`: Consensus voting strategy (`weighted_domain`, `borda_count`, `pessimistic_worst_case`, `simple_average`)
- `--record-trend`: Record review metrics to historical trend tracker
- `--deliberate`: Conduct multi-persona cross-examination deliberation round
- `--provider <name>`: Override default provider (`openai`, `anthropic`, `gemini`, `ollama`, `mock`)
- `--model, -m <model>`: Override model name
- `--output-md <file>`: Markdown report destination (default: `panel_review_report.md`)
- `--output-html <file>`: HTML dashboard destination (default: `panel_review_report.html`)
- `--output-json <file>`: JSON report destination
- `--output-sarif <file>`: SARIF v2.1.0 report destination for GitHub Security Code Scanning Alerts

---

## 📋 Available Review Presets

| Preset | Description | Active Personas |
| :--- | :--- | :--- |
| `security-strict` | AppSec & compliance audit with zero tolerance | Security Engineer, Compliance Specialist |
| `sre-readiness` | Production telemetry, error budgets & resilience | Observability Engineer, Performance Engineer |
| `clean-architecture` | Modularity, testability & SOLID design principles | Software Architect, QA Engineer |
| `quick-scan` | Rapid high-level health assessment | Security, Observability, Architect |
| `full-audit` | Complete board evaluation with all personas | All 6 Personas |

---

## 🧪 Testing

Run the comprehensive unit test suite:

```bash
python3 -m unittest discover -s tests
# or
make test
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
