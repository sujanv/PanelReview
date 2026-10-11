"""
Review engine orchestrating concurrent persona evaluations.
"""

import concurrent.futures
from typing import List, Optional, Callable
from panel_review.config import PanelConfig
from panel_review.models import (
    RepositoryInfo,
    PersonaReviewResult,
    ConsensusReport,
)
from panel_review.personas.base import Persona
from panel_review.personas.registry import PersonaRegistry
from panel_review.personas.chair import PanelChair
from panel_review.providers.factory import ProviderFactory


class ReviewEngine:
    def __init__(self, config: PanelConfig):
        self.config = config
        self.personas: List[Persona] = PersonaRegistry.load_personas(config)
        self.chair = PanelChair(
            chair_title=config.consensus.chair_title,
            chair_emoji=config.consensus.chair_emoji,
            min_approval_score=config.consensus.min_approval_score,
            critical_issues_block_approval=config.consensus.critical_issues_block_approval,
        )

    def run_review(
        self,
        repo_info: RepositoryInfo,
        on_persona_start: Optional[Callable[[Persona, str, str], None]] = None,
        on_persona_complete: Optional[Callable[[PersonaReviewResult], None]] = None,
        max_workers: int = 4,
    ) -> ConsensusReport:
        """
        Executes parallel reviews across all configured personas and synthesizes consensus.
        """
        if not repo_info.files:
            return self.chair.synthesize(repo_info, [])

        persona_results: List[PersonaReviewResult] = []

        def _evaluate_persona(persona: Persona) -> PersonaReviewResult:
            # Find persona config entry for model/provider override
            p_cfg = next((p for p in self.config.personas if p.id == persona.persona_id), None)
            prov_name = p_cfg.provider if (p_cfg and p_cfg.provider != "default") else self.config.default_provider
            mod_override = p_cfg.model if (p_cfg and p_cfg.model != "default") else None

            provider = ProviderFactory.create(prov_name, self.config, mod_override)
            model_name = provider.model

            if on_persona_start:
                on_persona_start(persona, prov_name, model_name)

            system_prompt = persona.build_system_prompt()
            review_prompt = persona.build_review_prompt(repo_info.files, repo_info)

            try:
                raw_response = provider.generate(review_prompt, system_prompt=system_prompt)
                result = persona.parse_llm_response(raw_response, model_used=f"{prov_name}:{model_name}")
            except Exception as e:
                # Fallback on failure
                result = PersonaReviewResult(
                    persona_id=persona.persona_id,
                    persona_name=persona.name,
                    persona_title=persona.title,
                    persona_emoji=persona.emoji,
                    model_used=f"{prov_name}:{model_name}",
                    summary=f"Evaluation failed due to error: {str(e)}",
                    score=50,
                    findings=[],
                )

            if on_persona_complete:
                on_persona_complete(result)

            return result

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_persona = {
                executor.submit(_evaluate_persona, p): p for p in self.personas
            }
            for future in concurrent.futures.as_completed(future_to_persona):
                res = future.result()
                persona_results.append(res)

        # Synthesize consensus
        chair_prov_name = self.config.consensus.provider
        chair_mod = self.config.consensus.model
        chair_provider = ProviderFactory.create(chair_prov_name, self.config, chair_mod)

        chair_prompt = self.chair.build_consensus_prompt(repo_info, persona_results)
        chair_system_prompt = (
            "You are the Panel Review Chair moderating an expert AI panel review. "
            "Synthesize consensus across security, observability, performance, architecture, QA, and compliance."
        )

        try:
            chair_raw = chair_provider.generate(chair_prompt, system_prompt=chair_system_prompt)
        except Exception:
            chair_raw = None

        consensus_report = self.chair.synthesize(
            repo_info=repo_info,
            persona_results=persona_results,
            llm_synthesis_text=chair_raw,
        )

        return consensus_report
