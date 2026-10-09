from setuptools import setup, find_packages

setup(
    name="panel-review",
    version="1.0.0",
    description="AI-based Multi-Persona Panel Review System for Polyglot Codebases",
    author="PanelReview Team",
    packages=find_packages(),
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "panel-review=panel_review.cli:main",
            "staged-push=scripts.staged_git_pusher:main",
        ],
    },
)
