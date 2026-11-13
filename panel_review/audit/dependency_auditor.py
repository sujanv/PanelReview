"""
Dependency Vulnerability and License Compliance Auditor.
Parses manifests and lockfiles across Python, Node.js, Go, and Rust ecosystems.
Audits for known vulnerable version signatures, copyleft license risks, and unpinned supply-chain hazards.
"""

import os
import re
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Tuple


class LicenseCategory(str, Enum):
    PERMISSIVE = "PERMISSIVE"  # MIT, Apache-2.0, BSD-2/3-Clause, ISC
    COPYLEFT = "COPYLEFT"      # GPL-2.0, GPL-3.0, AGPL-3.0, LGPL
    PROPRIETARY = "PROPRIETARY"
    UNKNOWN = "UNKNOWN"


@dataclass
class DependencyInfo:
    name: str
    version: str
    ecosystem: str
    manifest_file: str
    license_name: str = "Unknown"
    license_category: LicenseCategory = LicenseCategory.UNKNOWN
    is_unpinned: bool = False
    vulnerabilities: List[str] = field(default_factory=list)


@dataclass
class AuditReport:
    total_dependencies: int
    ecosystems_detected: List[str]
    permissive_count: int
    copyleft_count: int
    unknown_license_count: int
    unpinned_count: int
    vulnerable_count: int
    dependencies: List[DependencyInfo]
    findings: List[Dict[str, Any]]

    @property
    def has_critical_findings(self) -> bool:
        return self.vulnerable_count > 0 or self.copyleft_count > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_dependencies": self.total_dependencies,
            "ecosystems_detected": self.ecosystems_detected,
            "permissive_count": self.permissive_count,
            "copyleft_count": self.copyleft_count,
            "unknown_license_count": self.unknown_license_count,
            "unpinned_count": self.unpinned_count,
            "vulnerable_count": self.vulnerable_count,
            "has_critical_findings": self.has_critical_findings,
            "dependencies": [
                {
                    "name": d.name,
                    "version": d.version,
                    "ecosystem": d.ecosystem,
                    "manifest_file": d.manifest_file,
                    "license_name": d.license_name,
                    "license_category": d.license_category.value,
                    "is_unpinned": d.is_unpinned,
                    "vulnerabilities": d.vulnerabilities,
                }
                for d in self.dependencies
            ],
            "findings": self.findings,
        }


# Reference database of known vulnerable or dangerous package patterns
KNOWN_VULNERABLE_PATTERNS = [
    # Python
    {
        "ecosystem": "Python",
        "name_regex": r"^pycrypto$",
        "reason": "PyCrypto is unmaintained since 2013 and has critical known vulnerabilities. Replace with pycryptodome or cryptography.",
        "severity": "CRITICAL",
    },
    {
        "ecosystem": "Python",
        "name_regex": r"^telnetlib3?$",
        "reason": "Unencrypted Telnet protocol transmits credentials in plaintext. Replace with SSH or TLS.",
        "severity": "HIGH",
    },
    {
        "ecosystem": "Python",
        "name_regex": r"^urllib3$",
        "version_check": lambda v: v.startswith(("1.25", "1.26.0", "1.26.1", "1.26.2", "1.26.3", "1.26.4")),
        "reason": "urllib3 versions prior to 1.26.5 suffer from CVE-2021-33503 (ReDoS / proxy auth leak).",
        "severity": "HIGH",
    },
    {
        "ecosystem": "Python",
        "name_regex": r"^requests$",
        "version_check": lambda v: v.startswith(("2.0", "2.1", "2.2", "2.30")),
        "reason": "requests prior to 2.31.0 leaks Proxy-Authorization headers on HTTPS redirects (CVE-2023-32681).",
        "severity": "HIGH",
    },
    # JavaScript / Node.js
    {
        "ecosystem": "JavaScript",
        "name_regex": r"^lodash$",
        "version_check": lambda v: v.startswith(("3.", "4.17.0", "4.17.1", "4.17.20")),
        "reason": "lodash prior to 4.17.21 is vulnerable to Prototype Pollution (CVE-2021-23337, CVE-2020-8203).",
        "severity": "HIGH",
    },
    {
        "ecosystem": "JavaScript",
        "name_regex": r"^express$",
        "version_check": lambda v: v.startswith(("3.", "4.16", "4.17", "4.18")),
        "reason": "Express prior to 4.19.2 contains open redirect and path traversal vulnerabilities (CVE-2024-29041).",
        "severity": "HIGH",
    },
    {
        "ecosystem": "JavaScript",
        "name_regex": r"^jsonwebtoken$",
        "version_check": lambda v: v.startswith(("8.", "7.", "6.")),
        "reason": "jsonwebtoken < 9.0.0 is vulnerable to insecure key verification and algorithm confusion.",
        "severity": "HIGH",
    },
]

# Known license heuristics for common packages
KNOWN_LICENSES: Dict[str, Tuple[str, LicenseCategory]] = {
    # Permissive
    "requests": ("Apache-2.0", LicenseCategory.PERMISSIVE),
    "urllib3": ("MIT", LicenseCategory.PERMISSIVE),
    "flask": ("BSD-3-Clause", LicenseCategory.PERMISSIVE),
    "fastapi": ("MIT", LicenseCategory.PERMISSIVE),
    "pytest": ("MIT", LicenseCategory.PERMISSIVE),
    "express": ("MIT", LicenseCategory.PERMISSIVE),
    "lodash": ("MIT", LicenseCategory.PERMISSIVE),
    "react": ("MIT", LicenseCategory.PERMISSIVE),
    "gin": ("MIT", LicenseCategory.PERMISSIVE),
    "echo": ("MIT", LicenseCategory.PERMISSIVE),
    # Copyleft
    "gpl-module": ("GPL-3.0", LicenseCategory.COPYLEFT),
    "pygpl": ("GPL-2.0", LicenseCategory.COPYLEFT),
    "readline": ("GPL-3.0", LicenseCategory.COPYLEFT),
}


class DependencyAuditor:
    """Audits software dependencies across multiple programming language ecosystems."""

    @classmethod
    def audit_directory(cls, repo_path: str = ".") -> AuditReport:
        """Inspects all manifest and lock files found in the directory."""
        deps: List[DependencyInfo] = []
        ecosystems: Set[str] = set()

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "vendor", "__pycache__", ".venv")]
            for fn in files:
                full_path = os.path.join(root, fn)
                rel_path = os.path.relpath(full_path, repo_path)

                if fn == "requirements.txt":
                    parsed = cls._parse_requirements_txt(full_path, rel_path)
                    deps.extend(parsed)
                    if parsed:
                        ecosystems.add("Python")
                elif fn == "package.json":
                    parsed = cls._parse_package_json(full_path, rel_path)
                    deps.extend(parsed)
                    if parsed:
                        ecosystems.add("JavaScript")
                elif fn == "go.mod":
                    parsed = cls._parse_go_mod(full_path, rel_path)
                    deps.extend(parsed)
                    if parsed:
                        ecosystems.add("Go")
                elif fn == "Cargo.toml":
                    parsed = cls._parse_cargo_toml(full_path, rel_path)
                    deps.extend(parsed)
                    if parsed:
                        ecosystems.add("Rust")

        # Evaluate licenses and security vulnerabilities
        findings: List[Dict[str, Any]] = []
        permissive_cnt = 0
        copyleft_cnt = 0
        unknown_lic_cnt = 0
        unpinned_cnt = 0
        vulnerable_cnt = 0

        for d in deps:
            # License audit
            lic_name, lic_cat = cls._resolve_license(d.name)
            d.license_name = lic_name
            d.license_category = lic_cat

            if lic_cat == LicenseCategory.PERMISSIVE:
                permissive_cnt += 1
            elif lic_cat == LicenseCategory.COPYLEFT:
                copyleft_cnt += 1
                findings.append({
                    "type": "COPYLEFT_LICENSE_RISK",
                    "severity": "HIGH",
                    "package": d.name,
                    "version": d.version,
                    "license": lic_name,
                    "manifest": d.manifest_file,
                    "description": f"Package '{d.name}' uses copyleft license {lic_name}, which may mandate source disclosure under derivative work clauses.",
                    "remediation": "Audit organizational legal policy or replace with a permissive alternative (MIT/Apache-2.0/BSD).",
                })
            else:
                unknown_lic_cnt += 1

            # Unpinned supply chain hazard check
            if d.is_unpinned:
                unpinned_cnt += 1
                findings.append({
                    "type": "UNPINNED_DEPENDENCY",
                    "severity": "MEDIUM",
                    "package": d.name,
                    "version": d.version,
                    "manifest": d.manifest_file,
                    "description": f"Package '{d.name}' does not pin an exact immutable version, creating non-deterministic builds and supply-chain tampering risks.",
                    "remediation": "Pin the package to an exact version (e.g. 'pkg==1.2.3' or 'pkg@1.2.3').",
                })

            # Vulnerability check
            vulns = cls._check_vulnerabilities(d)
            if vulns:
                d.vulnerabilities.extend(vulns)
                vulnerable_cnt += 1
                for v in vulns:
                    findings.append({
                        "type": "KNOWN_VULNERABILITY",
                        "severity": "HIGH",
                        "package": d.name,
                        "version": d.version,
                        "manifest": d.manifest_file,
                        "description": v,
                        "remediation": f"Upgrade '{d.name}' to the latest patched release or remove the dependency.",
                    })

        return AuditReport(
            total_dependencies=len(deps),
            ecosystems_detected=sorted(list(ecosystems)),
            permissive_count=permissive_cnt,
            copyleft_count=copyleft_cnt,
            unknown_license_count=unknown_lic_cnt,
            unpinned_count=unpinned_cnt,
            vulnerable_count=vulnerable_cnt,
            dependencies=deps,
            findings=findings,
        )

    @classmethod
    def _resolve_license(cls, pkg_name: str) -> Tuple[str, LicenseCategory]:
        low = pkg_name.lower().strip()
        if low in KNOWN_LICENSES:
            return KNOWN_LICENSES[low]
        # Basic heuristic inference
        if "gpl" in low:
            return ("GPL-3.0", LicenseCategory.COPYLEFT)
        return ("Unknown / Unspecified", LicenseCategory.UNKNOWN)

    @classmethod
    def _check_vulnerabilities(cls, dep: DependencyInfo) -> List[str]:
        vulns = []
        for pat in KNOWN_VULNERABLE_PATTERNS:
            if pat["ecosystem"] == dep.ecosystem and re.search(pat["name_regex"], dep.name, re.IGNORECASE):
                if "version_check" in pat:
                    if pat["version_check"](dep.version):
                        vulns.append(pat["reason"])
                else:
                    vulns.append(pat["reason"])
        return vulns

    @classmethod
    def _parse_requirements_txt(cls, file_path: str, rel_path: str) -> List[DependencyInfo]:
        results = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("-"):
                        continue
                    # Match pkg==1.2.3, pkg>=1.2.3, pkg
                    m = re.match(r"^([a-zA-Z0-9_\-\.]+)(?:([=><~!]+)([^;\s]+))?", line)
                    if m:
                        name = m.group(1)
                        op = m.group(2)
                        ver = m.group(3) if m.group(3) else "unspecified"
                        is_unpinned = op is None or op != "=="
                        results.append(
                            DependencyInfo(
                                name=name,
                                version=ver,
                                ecosystem="Python",
                                manifest_file=rel_path,
                                is_unpinned=is_unpinned,
                            )
                        )
        except Exception:
            pass
        return results

    @classmethod
    def _parse_package_json(cls, file_path: str, rel_path: str) -> List[DependencyInfo]:
        results = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            deps = {}
            deps.update(data.get("dependencies", {}))
            deps.update(data.get("devDependencies", {}))

            for name, ver_str in deps.items():
                clean_ver = str(ver_str).strip()
                is_unpinned = clean_ver.startswith(("^", "~", ">", "*")) or clean_ver in ("latest", "*")
                norm_ver = re.sub(r"^[\^~>=<]+", "", clean_ver)
                results.append(
                    DependencyInfo(
                        name=name,
                        version=norm_ver if norm_ver else clean_ver,
                        ecosystem="JavaScript",
                        manifest_file=rel_path,
                        is_unpinned=is_unpinned,
                    )
                )
        except Exception:
            pass
        return results

    @classmethod
    def _parse_go_mod(cls, file_path: str, rel_path: str) -> List[DependencyInfo]:
        results = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                in_require = False
                for line in f:
                    line = line.strip()
                    if line.startswith("require ("):
                        in_require = True
                        continue
                    elif in_require and line == ")":
                        in_require = False
                        continue

                    if in_require or line.startswith("require "):
                        clean_line = line.replace("require ", "").strip()
                        parts = clean_line.split()
                        if len(parts) >= 2:
                            name = parts[0]
                            ver = parts[1]
                            results.append(
                                DependencyInfo(
                                    name=name,
                                    version=ver,
                                    ecosystem="Go",
                                    manifest_file=rel_path,
                                    is_unpinned=False,
                                )
                            )
        except Exception:
            pass
        return results

    @classmethod
    def _parse_cargo_toml(cls, file_path: str, rel_path: str) -> List[DependencyInfo]:
        results = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                in_deps = False
                for line in f:
                    line = line.strip()
                    if line.startswith("[dependencies]") or line.startswith("[dev-dependencies]"):
                        in_deps = True
                        continue
                    elif line.startswith("["):
                        in_deps = False
                        continue

                    if in_deps and "=" in line:
                        parts = line.split("=", 1)
                        name = parts[0].strip()
                        raw_ver = parts[1].strip().strip('"').strip("'")
                        ver_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', parts[1])
                        if ver_match:
                            ver = ver_match.group(1)
                        else:
                            ver = raw_ver
                        results.append(
                            DependencyInfo(
                                name=name,
                                version=ver,
                                ecosystem="Rust",
                                manifest_file=rel_path,
                                is_unpinned=ver in ("*", ""),
                            )
                        )
        except Exception:
            pass
        return results
