"""Miscellaneous helpers shared across quiz modules."""

from __future__ import annotations

from typing import Dict

from .models import QuizConfig


def trait_code_to_name(config: QuizConfig) -> Dict[str, str]:
    """Create a mapping from trait code to display name."""

    return {trait.code: trait.name for trait in config.traits}


def normalize_scores(config: QuizConfig, scores: Dict[str, float]) -> Dict[str, float]:
    """Normalize trait scores to the 0..1 range based on caps."""

    normalized: Dict[str, float] = {}
    for code, score in scores.items():
        cap = config.scoring.trait_caps.get(code, 1.0) or 1.0
        normalized[code] = min(score / cap, 1.0)
    return normalized
