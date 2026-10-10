"""
Performance & Scalability Engineer persona for algorithmic complexity, resource management, and concurrency.
"""

from typing import Optional, List
from panel_review.personas.base import Persona


class PerformanceEngineerPersona(Persona):
    def __init__(
        self,
        name: str = "Performance & Scalability Engineer",
        title: str = "Resource Efficiency & High-Throughput Specialist",
        emoji: str = "⚡",
        focus_areas: Optional[List[str]] = None,
        severity_threshold: str = "MEDIUM",
        custom_system_prompt: Optional[str] = None,
    ):
        defaults = [
            "Algorithmic time complexity (e.g. O(N^2) loops) and space complexity",
            "Memory allocations, buffer reuse, and memory leak vectors",
            "Database query efficiency, N+1 query patterns, missing index indicators",
            "Concurrency bottlenecks, thread contention, deadlocks, and race conditions",
            "Connection pooling and socket/file descriptor leaks",
            "Caching layer utilization, hot paths, and cache invalidation",
        ]
        super().__init__(
            persona_id="performance",
            name=name,
            title=title,
            emoji=emoji,
            focus_areas=focus_areas or defaults,
            severity_threshold=severity_threshold,
            custom_system_prompt=custom_system_prompt,
        )
