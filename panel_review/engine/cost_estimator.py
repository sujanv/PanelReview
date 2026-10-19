"""
Pre-Flight LLM Token & Cost Estimator.
Calculates token budgets and projected USD costs across configured AI model providers and personas.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import math


@dataclass
class ModelPricing:
    input_cost_per_1m: float   # USD per 1,000,000 input tokens
    output_cost_per_1m: float  # USD per 1,000,000 output tokens


# Standard reference pricing per 1M tokens
MODEL_PRICING: Dict[str, ModelPricing] = {
    # OpenAI
    "gpt-4o": ModelPricing(input_cost_per_1m=2.50, output_cost_per_1m=10.00),
    "gpt-4o-mini": ModelPricing(input_cost_per_1m=0.15, output_cost_per_1m=0.60),
    "o1": ModelPricing(input_cost_per_1m=15.00, output_cost_per_1m=60.00),
    "o3-mini": ModelPricing(input_cost_per_1m=1.10, output_cost_per_1m=4.40),
    # Anthropic
    "claude-3-7-sonnet": ModelPricing(input_cost_per_1m=3.00, output_cost_per_1m=15.00),
    "claude-3-5-sonnet": ModelPricing(input_cost_per_1m=3.00, output_cost_per_1m=15.00),
    "claude-3-5-sonnet-20241022": ModelPricing(input_cost_per_1m=3.00, output_cost_per_1m=15.00),
    "claude-3-haiku": ModelPricing(input_cost_per_1m=0.25, output_cost_per_1m=1.25),
    # Google Gemini
    "gemini-1.5-pro": ModelPricing(input_cost_per_1m=1.25, output_cost_per_1m=5.00),
    "gemini-1.5-flash": ModelPricing(input_cost_per_1m=0.075, output_cost_per_1m=0.30),
    "gemini-2.0-flash": ModelPricing(input_cost_per_1m=0.10, output_cost_per_1m=0.40),
    # Local & Offline (Free)
    "ollama": ModelPricing(input_cost_per_1m=0.0, output_cost_per_1m=0.0),
    "mock": ModelPricing(input_cost_per_1m=0.0, output_cost_per_1m=0.0),
}

DEFAULT_FALLBACK_PRICING = ModelPricing(input_cost_per_1m=2.00, output_cost_per_1m=8.00)


@dataclass
class PersonaCostEstimate:
    persona_id: str
    persona_name: str
    model: str
    input_tokens: int
    est_output_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float


@dataclass
class CostEstimateReport:
    total_files_scanned: int
    total_code_bytes: int
    codebase_input_tokens: int
    total_personas: int
    total_aggregate_input_tokens: int
    total_aggregate_output_tokens: int
    total_estimated_usd: float
    persona_breakdown: List[PersonaCostEstimate]
    file_token_breakdown: Dict[str, int]
    is_zero_cost: bool


class CostEstimator:
    """Estimates token consumption and financial cost for a proposed review run."""

    ESTIMATED_OUTPUT_TOKENS_PER_PERSONA = 1200
    PROMPT_OVERHEAD_TOKENS_PER_PERSONA = 450

    @staticmethod
    def estimate_tokens_from_text(text: str) -> int:
        """Approximates token count based on code character and whitespace density."""
        if not text:
            return 0
        # Average ~3.7 characters per token for source code
        return max(1, math.ceil(len(text) / 3.7))

    @classmethod
    def get_pricing(cls, model_name: str) -> ModelPricing:
        """Resolves pricing model for a given model identifier."""
        norm_name = model_name.lower().strip()
        for k, v in MODEL_PRICING.items():
            if k in norm_name:
                return v
        return DEFAULT_FALLBACK_PRICING

    @classmethod
    def estimate(
        cls,
        file_contents: Dict[str, str],
        personas_config: List[Dict],
        default_model: str = "claude-3-5-sonnet",
    ) -> CostEstimateReport:
        """Generates a complete token and cost projection."""
        file_tokens: Dict[str, int] = {}
        total_code_bytes = 0

        for path, content in file_contents.items():
            tokens = cls.estimate_tokens_from_text(content)
            file_tokens[path] = tokens
            total_code_bytes += len(content.encode("utf-8"))

        base_code_tokens = sum(file_tokens.values())

        active_personas = [p for p in personas_config if p.get("enabled", True)]
        if not active_personas:
            active_personas = [{"id": "chair", "name": "Review Chair", "model": default_model}]

        persona_estimates: List[PersonaCostEstimate] = []
        total_input_cost = 0.0
        total_output_cost = 0.0
        total_in_tokens = 0
        total_out_tokens = 0

        for p in active_personas:
            pid = p.get("id", "persona")
            pname = p.get("name", pid)
            pmodel = p.get("model") or default_model

            pricing = cls.get_pricing(pmodel)
            inp_tokens = base_code_tokens + cls.PROMPT_OVERHEAD_TOKENS_PER_PERSONA
            out_tokens = cls.ESTIMATED_OUTPUT_TOKENS_PER_PERSONA

            in_cost = (inp_tokens / 1_000_000) * pricing.input_cost_per_1m
            out_cost = (out_tokens / 1_000_000) * pricing.output_cost_per_1m
            tot_cost = in_cost + out_cost

            persona_estimates.append(
                PersonaCostEstimate(
                    persona_id=pid,
                    persona_name=pname,
                    model=pmodel,
                    input_tokens=inp_tokens,
                    est_output_tokens=out_tokens,
                    input_cost_usd=round(in_cost, 6),
                    output_cost_usd=round(out_cost, 6),
                    total_cost_usd=round(tot_cost, 6),
                )
            )

            total_in_tokens += inp_tokens
            total_out_tokens += out_tokens
            total_input_cost += in_cost
            total_output_cost += out_cost

        total_usd = total_input_cost + total_output_cost
        is_zero_cost = total_usd == 0.0

        return CostEstimateReport(
            total_files_scanned=len(file_contents),
            total_code_bytes=total_code_bytes,
            codebase_input_tokens=base_code_tokens,
            total_personas=len(active_personas),
            total_aggregate_input_tokens=total_in_tokens,
            total_aggregate_output_tokens=total_out_tokens,
            total_estimated_usd=round(total_usd, 4),
            persona_breakdown=persona_estimates,
            file_token_breakdown=file_tokens,
            is_zero_cost=is_zero_cost,
        )
