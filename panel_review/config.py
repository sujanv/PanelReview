"""
Configuration parser and validator for PanelReview.
"""

import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class ProviderConfig:
    name: str = "mock"
    model: str = "mock-expert-v1"
    base_url: Optional[str] = None
    api_key_env: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.2
    max_tokens: int = 4096


@dataclass
class ScannerConfig:
    max_file_size_kb: int = 512
    max_total_files: int = 100
    respect_gitignore: bool = True
    exclude_dirs: List[str] = field(default_factory=lambda: [
        ".git", "node_modules", "vendor", "dist", "build", "target",
        "__pycache__", ".venv", "venv", ".idea", ".vscode", "bin", "obj"
    ])
    exclude_files: List[str] = field(default_factory=lambda: [
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock",
        "poetry.lock", "go.sum", "*.min.js", "*.min.css", "*.map"
    ])


@dataclass
class PersonaConfig:
    id: str
    enabled: bool = True
    name: str = ""
    title: str = ""
    emoji: str = "🧑‍💻"
    provider: str = "default"
    model: str = "default"
    focus_areas: List[str] = field(default_factory=list)
    severity_threshold: str = "LOW"
    custom_system_prompt: Optional[str] = None


@dataclass
class ConsensusConfig:
    enabled: bool = True
    chair_title: str = "Panel Review Chair"
    chair_emoji: str = "⚖️"
    provider: str = "default"
    model: str = "default"
    min_approval_score: int = 75
    critical_issues_block_approval: bool = True


@dataclass
class PanelConfig:
    version: str = "1.0"
    default_provider: str = "mock"
    default_model: str = "mock-expert-v1"
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)
    scanner: ScannerConfig = field(default_factory=ScannerConfig)
    personas: List[PersonaConfig] = field(default_factory=list)
    consensus: ConsensusConfig = field(default_factory=ConsensusConfig)

    def get_provider_config(self, provider_name: str) -> ProviderConfig:
        target = self.default_provider if provider_name == "default" else provider_name
        if target in self.providers:
            return self.providers[target]
        return ProviderConfig(name=target, model=self.default_model)

    def get_persona_provider(self, persona: PersonaConfig) -> tuple[str, str]:
        """Returns (provider_name, model_name) for a given persona."""
        prov = self.default_provider if persona.provider == "default" else persona.provider
        prov_cfg = self.get_provider_config(prov)
        mod = prov_cfg.model if persona.model == "default" else persona.model
        return prov, mod

    def get_enabled_personas(self) -> List[PersonaConfig]:
        return [p for p in self.personas if p.enabled]


def _simple_yaml_parse(text: str) -> Dict[str, Any]:
    """
    Fallback basic YAML parser for standard key-value and list structures
    when PyYAML is not installed.
    """
    lines = text.splitlines()
    root: Dict[str, Any] = {}
    current_key = None
    list_target: Optional[List[Any]] = None
    dict_stack: List[tuple[int, Dict[str, Any]]] = [(0, root)]

    # If it is valid JSON, parse directly
    stripped = text.strip()
    if (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]")):
        return json.loads(text)

    # Simple line-by-line YAML parser for basic configs
    import re
    result: Dict[str, Any] = {}
    current_section = None
    current_list = None
    current_obj = None

    for line in lines:
        raw_line = line
        line = line.split("#")[0].rstrip()
        if not line:
            continue
        indent = len(line) - len(line.lstrip())
        content = line.strip()

        # Top level key
        if indent == 0 and ":" in content:
            k, v = content.split(":", 1)
            k = k.strip().strip('"').strip("'")
            v = v.strip().strip('"').strip("'")
            if v:
                result[k] = _coerce_val(v)
            else:
                result[k] = {}
            current_section = k
            current_list = None
            current_obj = None
        elif current_section is not None:
            # Sub-elements
            if content.startswith("- "):
                # List item
                val = content[2:].strip().strip('"').strip("'")
                if isinstance(result[current_section], dict) and not result[current_section]:
                    result[current_section] = []
                if isinstance(result[current_section], list):
                    result[current_section].append(_coerce_val(val))
            elif ":" in content:
                k, v = content.split(":", 1)
                k = k.strip().strip('"').strip("'")
                v = v.strip().strip('"').strip("'")
                if isinstance(result[current_section], dict):
                    result[current_section][k] = _coerce_val(v) if v else {}

    return result


def _coerce_val(v: str) -> Any:
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    if v.lower() in ("null", "none"):
        return None
    try:
        if "." in v:
            return float(v)
        return int(v)
    except ValueError:
        return v


def load_config(config_path: Optional[str] = None) -> PanelConfig:
    """
    Loads PanelConfig from file, trying the given path, or panel_config.yaml, or panel_config.json.
    """
    candidates = []
    if config_path:
        candidates.append(config_path)
    else:
        candidates.extend([
            "panel_config.json",
            "panel_config.yaml",
            "panel_config.yml",
            os.path.expanduser("~/.panel_review/config.json"),
            os.path.expanduser("~/.panel_review/config.yaml"),
        ])

    data: Dict[str, Any] = {}
    loaded_from = None

    for path in candidates:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if path.endswith(".json"):
                data = json.loads(content)
                loaded_from = path
                break
            elif path.endswith((".yaml", ".yml")):
                if HAS_YAML:
                    data = yaml.safe_load(content) or {}
                else:
                    data = _simple_yaml_parse(content)
                loaded_from = path
                break

    if not data:
        # Default fallback
        data = {
            "default_provider": "mock",
            "default_model": "mock-expert-v1",
        }

    # Environment overrides
    default_provider = os.getenv("PANEL_DEFAULT_PROVIDER", data.get("default_provider", "mock"))
    default_model = os.getenv("PANEL_DEFAULT_MODEL", data.get("default_model", "mock-expert-v1"))

    # Parse Providers
    providers_dict = {}
    for prov_name, prov_raw in data.get("providers", {}).items():
        if isinstance(prov_raw, dict):
            api_key_env = prov_raw.get("api_key_env")
            api_key = os.getenv(api_key_env) if api_key_env else None
            providers_dict[prov_name] = ProviderConfig(
                name=prov_name,
                model=prov_raw.get("model", default_model),
                base_url=prov_raw.get("base_url"),
                api_key_env=api_key_env,
                api_key=api_key,
                temperature=float(prov_raw.get("temperature", 0.2)),
                max_tokens=int(prov_raw.get("max_tokens", 4096)),
            )

    # Ensure mock is always registered
    if "mock" not in providers_dict:
        providers_dict["mock"] = ProviderConfig(name="mock", model="mock-expert-v1")

    # Parse Scanner
    raw_scanner = data.get("scanner", {})
    scanner_cfg = ScannerConfig(
        max_file_size_kb=int(raw_scanner.get("max_file_size_kb", 512)),
        max_total_files=int(raw_scanner.get("max_total_files", 100)),
        respect_gitignore=bool(raw_scanner.get("respect_gitignore", True)),
        exclude_dirs=raw_scanner.get("exclude_dirs", ScannerConfig().exclude_dirs),
        exclude_files=raw_scanner.get("exclude_files", ScannerConfig().exclude_files),
    )

    # Parse Personas
    personas_list = []
    for p_raw in data.get("personas", []):
        if isinstance(p_raw, dict):
            personas_list.append(PersonaConfig(
                id=p_raw.get("id", "persona"),
                enabled=bool(p_raw.get("enabled", True)),
                name=p_raw.get("name", "Reviewer"),
                title=p_raw.get("title", "Review Specialist"),
                emoji=p_raw.get("emoji", "🧑‍💻"),
                provider=p_raw.get("provider", "default"),
                model=p_raw.get("model", "default"),
                focus_areas=p_raw.get("focus_areas", []),
                severity_threshold=p_raw.get("severity_threshold", "LOW"),
                custom_system_prompt=p_raw.get("custom_system_prompt"),
            ))

    # Parse Consensus
    raw_con = data.get("consensus", {})
    consensus_cfg = ConsensusConfig(
        enabled=bool(raw_con.get("enabled", True)),
        chair_title=raw_con.get("chair_title", "Panel Review Chair"),
        chair_emoji=raw_con.get("chair_emoji", "⚖️"),
        provider=raw_con.get("provider", "default"),
        model=raw_con.get("model", "default"),
        min_approval_score=int(raw_con.get("min_approval_score", 75)),
        critical_issues_block_approval=bool(raw_con.get("critical_issues_block_approval", True)),
    )

    return PanelConfig(
        version=str(data.get("version", "1.0")),
        default_provider=default_provider,
        default_model=default_model,
        providers=providers_dict,
        scanner=scanner_cfg,
        personas=personas_list,
        consensus=consensus_cfg,
    )
