"""
Registry and factory for dynamically loading personas from configuration.
"""

from typing import List
from panel_review.config import PanelConfig, PersonaConfig
from panel_review.personas.base import Persona
from panel_review.personas.security import SecurityEngineerPersona
from panel_review.personas.observability import ObservabilityEngineerPersona
from panel_review.personas.performance import PerformanceEngineerPersona
from panel_review.personas.architecture import SoftwareArchitectPersona
from panel_review.personas.qa import QAEngineerPersona
from panel_review.personas.compliance import ComplianceEngineerPersona


BUILTIN_PERSONA_CLASSES = {
    "security": SecurityEngineerPersona,
    "observability": ObservabilityEngineerPersona,
    "performance": PerformanceEngineerPersona,
    "architecture": SoftwareArchitectPersona,
    "qa": QAEngineerPersona,
    "compliance": ComplianceEngineerPersona,
}


class PersonaRegistry:
    @staticmethod
    def load_personas(config: PanelConfig) -> List[Persona]:
        personas: List[Persona] = []
        enabled_configs = config.get_enabled_personas()

        for p_cfg in enabled_configs:
            pid = p_cfg.id.lower()
            if pid in BUILTIN_PERSONA_CLASSES:
                cls = BUILTIN_PERSONA_CLASSES[pid]
                instance = cls(
                    name=p_cfg.name or pid.title(),
                    title=p_cfg.title,
                    emoji=p_cfg.emoji,
                    focus_areas=p_cfg.focus_areas if p_cfg.focus_areas else None,
                    severity_threshold=p_cfg.severity_threshold,
                    custom_system_prompt=p_cfg.custom_system_prompt,
                )
            else:
                # Custom persona defined in config
                instance = Persona(
                    persona_id=p_cfg.id,
                    name=p_cfg.name or p_cfg.id,
                    title=p_cfg.title,
                    emoji=p_cfg.emoji,
                    focus_areas=p_cfg.focus_areas,
                    severity_threshold=p_cfg.severity_threshold,
                    custom_system_prompt=p_cfg.custom_system_prompt,
                )
            personas.append(instance)

        return personas
