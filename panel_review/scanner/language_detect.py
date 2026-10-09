"""
Language detection for polyglot codebases.
"""

import os
from typing import Optional

EXTENSION_MAP = {
    # Python
    ".py": "Python",
    ".pyi": "Python",
    # Go
    ".go": "Go",
    # Rust
    ".rs": "Rust",
    # TypeScript & JavaScript
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    # Java & JVM
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".scala": "Scala",
    ".groovy": "Groovy",
    # C & C++
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++ Header",
    # C# & .NET
    ".cs": "C#",
    ".fs": "F#",
    # Systems & Scripting
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".fish": "Shell",
    # Infrastructure & Data
    ".tf": "Terraform",
    ".hcl": "HCL",
    ".sql": "SQL",
    ".proto": "Protocol Buffers",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".xml": "XML",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".lua": "Lua",
    ".zig": "Zig",
    ".dart": "Dart",
    ".r": "R",
}

EXACT_FILENAME_MAP = {
    "dockerfile": "Dockerfile",
    "containerfile": "Dockerfile",
    "makefile": "Makefile",
    "cmakelists.txt": "CMake",
    "gemfile": "Ruby",
    "rakefile": "Ruby",
    "jenkinsfile": "Groovy",
    "vagrantfile": "Ruby",
}


def detect_language(file_path: str, first_line: Optional[str] = None) -> str:
    """
    Detects the programming or config language of a file based on name, extension, or shebang.
    """
    basename = os.path.basename(file_path).lower()

    if basename in EXACT_FILENAME_MAP:
        return EXACT_FILENAME_MAP[basename]
    if basename.startswith("dockerfile."):
        return "Dockerfile"

    _, ext = os.path.splitext(file_path)
    ext_lower = ext.lower()
    if ext_lower in EXTENSION_MAP:
        return EXTENSION_MAP[ext_lower]

    # Check shebang
    if first_line and first_line.startswith("#!"):
        shebang = first_line.lower()
        if "python" in shebang:
            return "Python"
        elif "node" in shebang or "bun" in shebang or "deno" in shebang:
            return "JavaScript"
        elif "bash" in shebang or "sh" in shebang or "zsh" in shebang:
            return "Shell"
        elif "ruby" in shebang:
            return "Ruby"
        elif "perl" in shebang:
            return "Perl"

    return "Plain Text / Other"


def is_likely_source_code(language: str) -> bool:
    """
    Returns True if the language represents program logic or infrastructure definition.
    """
    non_source = {"Plain Text / Other", "Markdown"}
    return language not in non_source
